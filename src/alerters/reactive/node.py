import logging
from datetime import timedelta
from typing import Optional

import dateutil.parser

from src.alerts.alerts import *
from src.channels.channel import ChannelSet
from src.store.redis.redis_api import RedisApi
from src.store.store_keys import *
from src.utils.config_parsers.internal import InternalConfig
from src.utils.config_parsers.internal_parsed import InternalConf
from src.utils.datetime import strfdelta
from src.utils.scaling import scale_to_giga, scale_to_nano
from src.utils.timing import TimedTaskLimiter, TimedOccurrenceTracker
from src.utils.types import NONE


class NodeType(Enum):
    VALIDATOR_FULL_NODE = 1,
    NON_VALIDATOR_FULL_NODE = 2


class Node:
    def __init__(self, name: str, api_url: Optional[str], prometheus_endpoint:
    Optional[str], node_type: NodeType, node_public_key:
    Optional[str], chain: str, redis: Optional[RedisApi],
                 is_archive_node: bool, consensus_public_key: str,
                 tendermint_address_key: str, staking_address: str,
                 entity_public_key: str,
                 internal_conf: InternalConfig = InternalConf) -> None:
        super().__init__()

        self.name = name
        self._api_url = api_url
        self._prometheus_endpoint = prometheus_endpoint
        self._node_type = node_type
        self._node_public_key = node_public_key
        self._chain = chain
        self._consensus_public_key = consensus_public_key
        self._tendermint_address_key = tendermint_address_key
        self._staking_address = staking_address
        self._entity_public_key = entity_public_key
        self._redis = redis
        self._redis_enabled = redis is not None
        self._redis_hash = Keys.get_hash_blockchain(self.chain)
        self._connected_to_api_server = True

        self._went_down_at = None
        self._bonded_balance = None
        self._debonding_balance = None
        self._shares_balance = None
        self._voting_power = None
        self._is_syncing = False
        self._no_of_peers = None
        self._initial_downtime_alert_sent = False

        self._no_change_in_height_warning_sent = False
        self._active = None
        self._is_missing_blocks = False
        self._finalized_block_height = 0
        self._time_of_last_height_check_activity = NONE
        self._time_of_last_height_change = NONE
        self._consecutive_blocks_missed = 0

        self._is_archive_node = is_archive_node

        self._validator_peer_danger_boundary = \
            internal_conf.validator_peer_danger_boundary

        self._validator_peer_safe_boundary = \
            internal_conf.validator_peer_safe_boundary

        self._full_node_peer_danger_boundary = \
            internal_conf.full_node_peer_danger_boundary

        self._no_change_in_height_first_warning_seconds = \
            internal_conf.no_change_in_height_first_warning_seconds

        self._no_change_in_height_interval_seconds = \
            internal_conf.no_change_in_height_interval_seconds

        self._downtime_alert_limiter = TimedTaskLimiter(
            internal_conf.downtime_alert_interval_seconds)

        self._finalized_height_alert_limiter = TimedTaskLimiter(
            timedelta(seconds=int(self._no_change_in_height_interval_seconds)))

        self._change_in_bonded_balance_threshold = \
            internal_conf.change_in_bonded_balance_threshold

        self._change_in_debonding_balance_threshold = \
            internal_conf.change_in_debonding_balance_threshold

        self._change_in_shares_balance_threshold = \
            internal_conf.change_in_shares_balance_threshold

        self._missed_blocks_danger_boundary = \
            internal_conf.missed_blocks_danger_boundary

        self._timed_block_miss_tracker = TimedOccurrenceTracker(
            internal_conf.max_missed_blocks_in_time_interval,
            internal_conf.max_missed_blocks_time_interval)

    def __str__(self) -> str:
        return self.name

    @property
    def voting_power(self) -> int:
        return self._voting_power

    @property
    def is_validator(self) -> bool:
        return self._node_type == NodeType.VALIDATOR_FULL_NODE

    @property
    def is_archive_node(self) -> bool:
        return self._is_archive_node

    @property
    def is_down(self) -> bool:
        return self._went_down_at is not None

    @property
    def is_active(self) -> bool:
        return self._active

    @property
    def is_missing_blocks(self) -> bool:
        return self.consecutive_blocks_missed_so_far > 0

    @property
    def consecutive_blocks_missed_so_far(self) -> int:
        return self._consecutive_blocks_missed

    @property
    def is_syncing(self) -> bool:
        return self._is_syncing

    @property
    def bonded_balance(self) -> int:
        return self._bonded_balance

    @property
    def debonding_balance(self) -> int:
        return self._debonding_balance

    @property
    def shares_balance(self) -> int:
        return self._shares_balance

    @property
    def finalized_height_alert_limiter(self) -> TimedTaskLimiter:
        return self._finalized_height_alert_limiter

    @property
    def node_public_key(self) -> str:
        return self._node_public_key

    @property
    def staking_address(self) -> str:
        return self._staking_address

    @property
    def api_url(self) -> str:
        return self._api_url

    @property
    def prometheus_endpoint(self) -> str:
        return self._prometheus_endpoint

    @property
    def chain(self) -> str:
        return self._chain

    @property
    def entity_public_key(self) -> str:
        return self._entity_public_key

    @property
    def is_connected_to_api_server(self) -> bool:
        return self._connected_to_api_server

    @property
    def consensus_public_key(self) -> str:
        return self._consensus_public_key

    @property
    def tendermint_address_key(self) -> str:
        return self._tendermint_address_key

    @property
    def no_of_peers(self) -> int:
        return self._no_of_peers

    @property
    def is_no_change_in_height_warning_sent(self) -> bool:
        return self._no_change_in_height_warning_sent

    @property
    def finalized_block_height(self) -> int:
        return self._finalized_block_height

    def status(self) -> str:
        return "bonded_balance={}, debonding_balance={}, shares_balance={}," \
               " is_syncing={}, no_of_peers={}, active={}, " \
               "finalized_block_height={}, is_missing_blocks={}" \
            .format(self.bonded_balance, self.debonding_balance,
                    self.shares_balance, self.is_syncing, self.no_of_peers,
                    self.is_active, self.finalized_block_height,
                    self.is_missing_blocks)

    def load_state(self, logger: logging.Logger) -> None:
        # If Redis is enabled, load any previously stored state
        if self._redis_enabled:

            self._went_down_at = self._redis.hget(
                self._redis_hash, Keys.get_node_went_down_at(self.name), None)

            self._bonded_balance = self._redis.hget_int(
                self._redis_hash, Keys.get_node_bonded_balance(self.name), None)

            self._debonding_balance = self._redis.hget_int(
                self._redis_hash, Keys.get_node_debonding_balance(self.name),
                None)

            self._shares_balance = self._redis.hget_int(
                self._redis_hash, Keys.get_node_shares_balance(self.name),
                None)

            self._is_syncing = self._redis.hget_bool(
                self._redis_hash, Keys.get_node_is_syncing(self.name), False)

            self._voting_power = self._redis.hget_int(
                self._redis_hash, Keys.get_voting_power(self.name), None)

            self._consecutive_blocks_missed = self._redis.hget_int(
                self._redis_hash, Keys.get_consecutive_blocks_missed(
                    self.name),
                0)

            self._no_of_peers = self._redis.hget_int(
                self._redis_hash, Keys.get_node_no_of_peers(self.name), None)

            self._active = self._redis.hget_bool(
                self._redis_hash, Keys.get_node_active(self.name), None)

            self._is_missing_blocks = self._redis.hget_bool(
                self._redis_hash, Keys.get_node_is_missing_blocks(self.name),
                False)

            self._time_of_last_height_check_activity = float(self._redis.hget(
                self._redis_hash,
                Keys.get_node_time_of_last_height_check_activity(self.name),
                NONE))

            self._time_of_last_height_change = float(self._redis.hget(
                self._redis_hash,
                Keys.get_node_time_of_last_height_change(self.name), NONE))

            self._finalized_block_height = self._redis.hget_int(
                self._redis_hash,
                Keys.get_node_finalized_block_height(self.name), 0)

            self._no_change_in_height_warning_sent = self._redis.hget_bool(
                self._redis_hash,
                Keys.get_node_no_change_in_height_warning_sent(self.name),
                False)

            if self._time_of_last_height_check_activity != NONE:
                self._finalized_height_alert_limiter.set_last_time_that_did_task(
                    datetime.fromtimestamp(
                        self._time_of_last_height_check_activity))
            else:
                self._finalized_height_alert_limiter.did_task()
                self._time_of_last_height_change = datetime.now().timestamp()

            # String to actual values
            if self._went_down_at is not None:
                try:
                    self._went_down_at = \
                        dateutil.parser.parse(self._went_down_at)
                except (TypeError, ValueError) as e:
                    logger.error('Error when parsing '
                                 '_went_down_at: %s', e)
                    self._went_down_at = None

            logger.debug(
                'Restored %s state: _went_down_at=%s,  _bonded_balance=%s, '
                '_debonding_balance=%s, _shares_balance=%s, _is_syncing=%s, '
                '_no_of_peers=%s, _active=%s, _no_of_blocks_missed=%s, '
                '_time_of_last_height_change=%s, '
                '_time_of_last_height_check_activity=%s, '
                '_finalized_block_height=%s, '
                '_no_change_in_height_warning_sent=%s, '
                '_is_missing_blocks=%s ',
                self.name, self._went_down_at, self._bonded_balance,
                self._debonding_balance, self._shares_balance,
                self._is_syncing, self._no_of_peers,
                self._active, self._consecutive_blocks_missed,
                self._time_of_last_height_change,
                self._time_of_last_height_check_activity,
                self._finalized_block_height,
                self._no_change_in_height_warning_sent,
                self.is_missing_blocks)

    def save_state(self, logger: logging.Logger) -> None:
        # If Redis is enabled, store the current state
        if self._redis_enabled:
            logger.debug(
                'Saved %s state: _went_down_at=%s,  _bonded_balance=%s, '
                '_debonding_balance=%s, _shares_balance=%s, _is_syncing=%s, '
                '_no_of_peers=%s, _active=%s, _no_of_blocks_missed=%s, '
                '_time_of_last_height_change=%s, '
                '_time_of_last_height_check_activity=%s, '
                '_finalized_block_height=%s, '
                '_no_change_in_height_warning_sent=%s, '
                '_is_missing_blocks=%s',
                self.name, self._went_down_at, self._bonded_balance,
                self._debonding_balance, self._shares_balance, self._is_syncing,
                self._no_of_peers, self._active,
                self._consecutive_blocks_missed,
                self._time_of_last_height_change,
                self._time_of_last_height_check_activity,
                self._finalized_block_height,
                self._no_change_in_height_warning_sent,
                self.is_missing_blocks)

            # Set values
            self._redis.hset_multiple(self._redis_hash, {
                Keys.get_node_went_down_at(self.name): str(self._went_down_at),
                Keys.get_node_bonded_balance(self.name): self._bonded_balance,
                Keys.get_node_debonding_balance(self.name):
                    self._debonding_balance,
                Keys.get_node_shares_balance(self.name):
                    self._shares_balance,
                Keys.get_node_is_syncing(self.name): str(self._is_syncing),
                Keys.get_node_no_of_peers(self.name): self._no_of_peers,
                Keys.get_voting_power(self.name): self._voting_power,
                Keys.get_consecutive_blocks_missed(self.name):
                    self._consecutive_blocks_missed,
                Keys.get_node_is_missing_blocks(self.name):
                    str(self.is_missing_blocks),
                Keys.get_node_active(self.name): str(self._active),
                Keys.get_node_time_of_last_height_check_activity(self.name):
                    self._time_of_last_height_check_activity,
                Keys.get_node_time_of_last_height_change(self.name):
                    self._time_of_last_height_change,
                Keys.get_node_finalized_block_height(self.name):
                    self._finalized_block_height,
                Keys.get_node_no_change_in_height_warning_sent(self.name):
                    str(self._no_change_in_height_warning_sent),
            })

    def set_as_down(self, channels: ChannelSet, logger: logging.Logger) -> None:

        logger.debug('%s set_as_down: is_down(currently)=%s, channels=%s',
                     self, self.is_down, channels)

        # Alert (varies depending on whether was already down)
        if self.is_down and not self._initial_downtime_alert_sent:
            if self.is_validator:
                channels.alert_critical(CannotAccessNodeAlert(self.name))
            else:
                channels.alert_warning(CannotAccessNodeAlert(self.name))
            self._downtime_alert_limiter.did_task()
            self._initial_downtime_alert_sent = True
        elif self.is_down and self._downtime_alert_limiter.can_do_task():
            went_down_at = datetime.fromtimestamp(self._went_down_at)
            downtime = strfdelta(datetime.now() - went_down_at,
                                 "{hours}h, {minutes}m, {seconds}s")
            if self.is_validator:
                channels.alert_critical(StillCannotAccessNodeAlert(
                    self.name, went_down_at, downtime))
            else:
                channels.alert_warning(StillCannotAccessNodeAlert(
                    self.name, went_down_at, downtime))
            self._downtime_alert_limiter.did_task()
        elif not self.is_down:
            # Do not alert for now just in case this is a connection hiccup
            channels.alert_info(ExperiencingDelaysAlert(self.name))
            self._went_down_at = datetime.now().timestamp()
            self._initial_downtime_alert_sent = False

    def set_as_up(self, channels: ChannelSet, logger: logging.Logger) -> None:

        logger.debug('%s set_as_up: is_down(currently)=%s, channels=%s',
                     self, self.is_down, channels)

        # Alert if node was down
        if self.is_down:
            # Only send accessible alert if inaccessible alert was sent
            if self._initial_downtime_alert_sent:
                went_down_at = datetime.fromtimestamp(self._went_down_at)
                downtime = strfdelta(datetime.now() - went_down_at,
                                     "{hours}h, {minutes}m, {seconds}s")
                channels.alert_info(NowAccessibleAlert(
                    self.name, went_down_at, downtime))

            # Reset downtime-related values
            self._downtime_alert_limiter.reset()
            self._went_down_at = None

    def set_bonded_balance(self, new_bonded_balance: int, channels: ChannelSet,
                           logger: logging.Logger) -> None:

        logger.debug(
            '%s set_bonded_balance: before=%s, new=%s, channels=%s',
            self, self.bonded_balance, new_bonded_balance, channels)

        # Alert if bonded_balance has changed
        if self.bonded_balance not in [None, new_bonded_balance]:
            # Extracted data is in giga, therefore, to give more meaningful
            # alerts, the bonded balance will be scaled down.
            threshold = scale_to_giga(self._change_in_bonded_balance_threshold)
            scaled_new_bal = round(scale_to_nano(new_bonded_balance), 3)
            scaled_bal = round(scale_to_nano(self.bonded_balance), 3)

            if self.is_validator and new_bonded_balance == 0:  # N to 0
                channels.alert_critical(BondedBalanceDecreasedAlert(
                    self.name, scaled_bal, scaled_new_bal))
            elif self.is_validator and self.bonded_balance == 0:  # 0 to N
                channels.alert_info(BondedBalanceIncreasedAlert(
                    self.name, scaled_bal, scaled_new_bal))
            else:  # Any change
                diff = new_bonded_balance - self.bonded_balance
                if abs(diff) > threshold:
                    if diff > 0:
                        channels.alert_info(BondedBalanceIncreasedByAlert(
                            self.name, scaled_bal, scaled_new_bal))
                    else:
                        channels.alert_info(BondedBalanceDecreasedByAlert(
                            self.name, scaled_bal, scaled_new_bal))

        # Update bonded balance
        self._bonded_balance = new_bonded_balance

    def set_debonding_balance(self, new_debonding_balance: int, \
                              channels: ChannelSet,
                              logger: logging.Logger) -> None:

        logger.debug(
            '%s set_debonding_balance: before=%s, new=%s, channels=%s',
            self, self.debonding_balance, new_debonding_balance, channels)

        # Alert if debonding_balance has changed
        if self.debonding_balance not in [None, new_debonding_balance]:
            # Extracted data is in giga, therefore, to give more meaningful
            # alerts, the debonding balance will be scaled down.
            threshold = scale_to_giga(
                self._change_in_debonding_balance_threshold)
            scaled_new_bal = round(scale_to_nano(new_debonding_balance), 3)
            scaled_bal = round(scale_to_nano(self.debonding_balance), 3)

            if self.is_validator and new_debonding_balance == 0:  # N to 0
                channels.alert_info(DebondingBalanceDecreasedAlert(
                    self.name, scaled_bal, scaled_new_bal))
            elif self.is_validator and self.debonding_balance == 0:  # 0 to N
                channels.alert_info(DebondingBalanceIncreasedAlert(
                    self.name, scaled_bal, scaled_new_bal))
            else:  # Any change
                diff = new_debonding_balance - self.debonding_balance
                if abs(diff) > threshold:
                    if diff > 0:
                        channels.alert_info(DebondingBalanceIncreasedByAlert(
                            self.name, scaled_bal, scaled_new_bal))
                    else:
                        channels.alert_info(DebondingBalanceDecreasedByAlert(
                            self.name, scaled_bal, scaled_new_bal))

        # Update debonding balance
        self._debonding_balance = new_debonding_balance

    def set_shares_balance(self, new_shares_balance: int, \
                           channels: ChannelSet,
                           logger: logging.Logger) -> None:

        logger.debug(
            '%s set_shares_balance: before=%s, new=%s, channels=%s',
            self, self.shares_balance, new_shares_balance, channels)

        # Alert if shares_balance has changed
        if self.shares_balance not in [None, new_shares_balance]:
            # Extracted data is in giga, therefore, to give more meaningful
            # alerts, the debonding balance will be scaled down.
            threshold = scale_to_giga(self._change_in_shares_balance_threshold)
            scaled_new_bal = round(scale_to_nano(new_shares_balance), 3)
            scaled_bal = round(scale_to_nano(self.shares_balance), 3)

            if self.is_validator and new_shares_balance == 0:  # N to 0
                channels.alert_info(SharesBalanceDecreasedAlert(
                    self.name, scaled_bal, scaled_new_bal))
            elif self.is_validator and self.shares_balance == 0:  # 0 to N
                channels.alert_info(SharesBalanceIncreasedAlert(
                    self.name, scaled_bal, scaled_new_bal))
            else:  # Any change
                diff = new_shares_balance - self.shares_balance
                if abs(diff) > threshold:
                    if diff > 0:
                        channels.alert_info(SharesBalanceIncreasedByAlert(
                            self.name, scaled_bal, scaled_new_bal))
                    else:
                        channels.alert_info(SharesBalanceDecreasedByAlert(
                            self.name, scaled_bal, scaled_new_bal))

        # Update shares balance
        self._shares_balance = new_shares_balance

    def set_is_syncing(self, now_is_syncing: bool, channels: ChannelSet,
                       logger: logging.Logger) -> None:
        logger.debug(
            '%s set_is_syncing: before=%s, new=%s, channels=%s',
            self, self.is_syncing, now_is_syncing, channels)

        # Alert if is syncing has changed
        if not self.is_syncing and now_is_syncing:
            channels.alert_warning(IsSyncingAlert(self.name))
        elif self.is_syncing and not now_is_syncing:
            channels.alert_info(IsNoLongerSyncingAlert(self.name))

        # Update is-syncing
        self._is_syncing = now_is_syncing

    def set_voting_power(self, new_voting_power: int, channels: ChannelSet,
                         logger: logging.Logger) -> None:
        # NOTE: This function assumes that the node is a validator

        logger.debug(
            '%s set_voting_power: before=%s, new=%s, channels=%s',
            self, self.voting_power, new_voting_power, channels)

        # Alert if voting power has changed
        if self.voting_power not in [None, new_voting_power]:
            if self.is_validator and new_voting_power == 0:  # N to 0
                channels.alert_critical(VotingPowerDecreasedAlert(
                    self.name, self.voting_power, new_voting_power))
            elif self.is_validator and self.voting_power == 0:  # 0 to N
                channels.alert_info(VotingPowerIncreasedAlert(
                    self.name, self.voting_power, new_voting_power))
            else:  # Any change
                diff = new_voting_power - self.voting_power
                if diff > 0:
                    channels.alert_info(VotingPowerIncreasedByAlert(
                        self.name, self.voting_power, new_voting_power))
                else:
                    channels.alert_info(VotingPowerDecreasedByAlert(
                        self.name, self.voting_power, new_voting_power))

        # Update voting power
        self._voting_power = new_voting_power

    def set_no_of_peers(self, new_no_of_peers: int, channels: ChannelSet,
                        logger: logging.Logger) -> None:

        logger.debug(
            '%s set_no_of_peers: before=%s, new=%s, channels=%s',
            self, self.no_of_peers, new_no_of_peers, channels)

        # Variable alias for improved readability
        if self.is_validator:
            danger = self._validator_peer_danger_boundary
            safe = self._validator_peer_safe_boundary
        else:
            danger = self._full_node_peer_danger_boundary
            safe = None

        # Alert if number of peers has changed
        if self.no_of_peers not in [None, new_no_of_peers]:
            if self.is_validator:
                if new_no_of_peers <= self._validator_peer_safe_boundary:
                    # beneath safe boundary
                    if new_no_of_peers > self.no_of_peers:  # increase
                        channels.alert_info(PeersIncreasedAlert(
                            self.name, self.no_of_peers, new_no_of_peers))
                    elif new_no_of_peers > danger:
                        # decrease outside danger range
                        channels.alert_warning(PeersDecreasedAlert(
                            self.name, self.no_of_peers, new_no_of_peers))
                    else:  # decrease inside danger range
                        channels.alert_critical(PeersDecreasedAlert(
                            self.name, self.no_of_peers, new_no_of_peers))
                elif self._no_of_peers <= self._validator_peer_safe_boundary \
                        < new_no_of_peers:
                    # increase outside safe range for the first time
                    channels.alert_info(
                        PeersIncreasedOutsideSafeRangeAlert(self.name, safe))
            else:
                if new_no_of_peers > self.no_of_peers:  # increase
                    if new_no_of_peers <= danger:
                        # increase inside danger range
                        channels.alert_info(PeersIncreasedAlert(
                            self.name, self.no_of_peers, new_no_of_peers))
                    elif self.no_of_peers <= danger < new_no_of_peers:
                        # increase outside danger range
                        channels.alert_info(
                            PeersIncreasedOutsideDangerRangeAlert(
                                self.name, danger))
                elif new_no_of_peers > danger:  # decrease outside danger range
                    pass
                else:  # decrease inside danger range
                    channels.alert_warning(PeersDecreasedAlert(
                        self.name, self.no_of_peers, new_no_of_peers))

        # Update number of peers
        self._no_of_peers = new_no_of_peers

    def set_active(self, now_is_active: bool, channels: ChannelSet,
                   logger: logging.Logger) -> None:
        # NOTE: This function assumes that the node is a validator.

        logger.debug('%s set_active: active(currently)=%s, channels=%s',
                     self, self.is_active, channels)

        if self.is_active not in [now_is_active, None]:
            if now_is_active:
                channels.alert_info(ValidatorIsNowActiveAlert(self.name))
            else:
                channels.alert_critical(ValidatorIsNotActiveAlert(self.name))
        self._active = now_is_active

    def update_finalized_block_height(self, new_finalized_height: int,
                                      logger: logging.Logger,
                                      channels: ChannelSet):

        logger.debug('%s update_finalized_block_height: finalized_block_height'
                     ' (currently)=%s', self, self._finalized_block_height)

        current_timestamp = datetime.now().timestamp()

        if self._finalized_block_height != new_finalized_height:

            if self.is_no_change_in_height_warning_sent:
                self._no_change_in_height_warning_sent = False
                channels.alert_info(
                    NodeFinalizedBlockHeightHasNowBeenUpdatedAlert(self.name))

            if self._finalized_block_height > new_finalized_height:
                logger.info('The finalized height of node {} decreased to {}.'
                            .format(self, self._finalized_block_height))

            self._finalized_block_height = new_finalized_height
            self._time_of_last_height_change = current_timestamp
            self._time_of_last_height_check_activity = current_timestamp
            self._finalized_height_alert_limiter.set_last_time_that_did_task(
                datetime.fromtimestamp(current_timestamp))
        else:

            timestamp_difference = current_timestamp - \
                                   self._time_of_last_height_change

            time_interval = strfdelta(timedelta(seconds=int(
                timestamp_difference)), "{hours}h, {minutes}m, {seconds}s")

            if not self.is_no_change_in_height_warning_sent and \
                    timestamp_difference > \
                    self._no_change_in_height_first_warning_seconds:

                self._no_change_in_height_warning_sent = True
                channels.alert_warning(
                    NodeFinalizedBlockHeightDidNotChangeInAlert(self.name,
                                                                time_interval))

            elif self._finalized_height_alert_limiter.can_do_task() and \
                    self.is_no_change_in_height_warning_sent:
                if self.is_validator:
                    channels.alert_critical(
                        NodeFinalizedBlockHeightDidNotChangeInAlert(
                            self.name, time_interval))
                else:
                    channels.alert_warning(
                        NodeFinalizedBlockHeightDidNotChangeInAlert(
                            self.name, time_interval))
                self._time_of_last_height_check_activity = current_timestamp
                self._finalized_height_alert_limiter. \
                    set_last_time_that_did_task(
                    datetime.fromtimestamp(current_timestamp))

    def add_missed_block(self, block_height: int, block_time: datetime,
                         missing_validators: int, channels: ChannelSet,
                         logger: logging.Logger) -> None:
        # NOTE: This function assumes that the node is a validator

        # Calculate the actual blocks missed as of when this function was called
        blocks_missed = self._consecutive_blocks_missed + 1

        # Variable alias for improved readability
        danger = self._missed_blocks_danger_boundary

        logger.debug(
            '%s add_missed_block: before=%s, new=%s, missing_validators = %s, '
            'channels=%s', self, self.consecutive_blocks_missed_so_far,
            blocks_missed, missing_validators, channels)

        # Let timed tracker know that block missed
        self._timed_block_miss_tracker.action_happened(at_time=block_time)
        # Alert (varies depending on whether was already missing blocks)
        if not self.is_missing_blocks:
            pass  # Do not alert on first missed block
        elif 2 <= blocks_missed < danger:
            channels.alert_info(MissedBlocksAlert(
                self.name, blocks_missed, block_height, missing_validators)
            )  # 2+ blocks missed inside danger range
        elif blocks_missed == 5:
            channels.alert_warning(MissedBlocksAlert(
                self.name, blocks_missed, block_height, missing_validators)
            )  # reached danger range
        elif blocks_missed >= max(10, danger) and blocks_missed % 10 == 0:
            channels.alert_critical(MissedBlocksAlert(
                self.name, blocks_missed, block_height, missing_validators)
            )  # Every (10N)th block missed for N >= 1 inside danger range
            self._timed_block_miss_tracker.reset()

        if self._timed_block_miss_tracker.too_many_occurrences(block_time):
            blocks_in_interval = self._timed_block_miss_tracker.max_occurrences
            time_interval = self._timed_block_miss_tracker.time_interval_pretty
            channels.alert_critical(TimedMissedBlocksAlert(
                self.name, blocks_in_interval, time_interval,
                block_height, missing_validators)
            )  # More blocks missed than is acceptable in the time interval
            self._timed_block_miss_tracker.reset()

        # Update consecutive blocks missed
        self._consecutive_blocks_missed = blocks_missed

    def clear_missed_blocks(self, channels: ChannelSet,
                            logger: logging.Logger) -> None:
        # NOTE: This function assumes that the node is a validator

        logger.debug(
            '%s clear_missed_blocks: channels=%s', self, channels)

        # Alert if validator was missing blocks (only if more than 1 block)
        if self.is_missing_blocks and self._consecutive_blocks_missed > 1:
            channels.alert_info(NoLongerMissingBlocksAlert(
                self.name, self._consecutive_blocks_missed))

        # Reset missed blocks related values
        self._consecutive_blocks_missed = 0

    # Categorise the event and alert as needed
    def process_event(self, event_height: str, event: dict,
                      channels: ChannelSet, logger: logging.Logger):

        # An escrow event is when tokens are either taken/added or reclaimed
        # from a delegation.
        if self._check_dict_path(event, 'escrow'):

            # Escrow events that take are usually done by the blockchain,
            # such as when a validator is slashed
            if self._check_dict_path(event, 'escrow', 'take'):
                if event['escrow']['take']['owner'] == self.entity_public_key:
                    tokens = event['escrow']['take']['amount']

                    logger.debug('%s Node %s Slashed %s tokens at height %s',
                                 self, self.name, tokens, event_height)
                    channels.alert_critical(SlashedAlert(
                        self.name, tokens, event_height))

            # Escrow events that add occur when someone delegates tokens to a
            # validator.
            elif self._check_dict_path(event, 'escrow', 'add'):
                if event['escrow']['add']['owner'] == self.entity_public_key:
                    tokens = event['escrow']['add']['amount']
                    escrow = event['escrow']['add']['escrow']

                    logger.debug('%s Node %s : Added %s tokens at height %s to '
                                 '%s .', self, self.name, tokens, event_height, \
                                 escrow)
                    channels.alert_info(EscrowAddEventSelfOwner(
                        self.name, tokens, event_height, escrow))

                elif event['escrow']['add']['escrow'] == self.entity_public_key:
                    tokens = event['escrow']['add']['amount']
                    owner = event['escrow']['add']['owner']

                    logger.debug('%s Node %s : Added %s tokens at height %s to '
                                 '%s .', self, self.name, tokens, event_height, \
                                 owner)
                    channels.alert_info(EscrowAddEventSelfEscrow(
                        self.name, tokens, event_height, owner))

            # Escrow events that reclaim occur when someone takes back their
            # delegated tokens from a validator
            elif self._check_dict_path(event, 'escrow', 'reclaim'):
                if event['escrow']['reclaim']['owner'] == \
                        self.entity_public_key:
                    tokens = event['escrow']['reclaim']['amount']
                    escrow = event['escrow']['reclaim']['escrow']

                    logger.debug('%s Node %s : reclaimed %s tokens at height %s'
                                 'to  %s .', self, self.name, tokens, \
                                 event_height, escrow)
                    channels.alert_info(EscrowReclaimEventSelfOwner(
                        self.name, tokens, event_height, escrow))

                elif event['escrow']['reclaim']['escrow'] == \
                        self.entity_public_key:
                    tokens = event['escrow']['reclaim']['amount']
                    owner = event['escrow']['reclaim']['owner']

                    logger.debug('%s Node %s : reclaimed %s tokens at height %s'
                                 'to  %s .', self, self.name, tokens, \
                                 event_height, owner)
                    channels.alert_info(EscrowReclaimEventSelfEscrow(
                        self.name, tokens, event_height, owner))

        # Burn events occur when a user decides to destroy their own tokens.
        elif self._check_dict_path(event, 'burn'):
            if event['burn']['owner'] == self.entity_public_key:
                tokens = event['burn']['amount']

                logger.debug('%s Node %s Burned %s tokens at height %s', self,
                             self.name, tokens, event_height)
                channels.alert_critical(TokensBurnedAlert(
                    self.name,
                    tokens,
                    event_height))

        # Transfer events occur when a user decides to send tokens to another
        # address.
        elif self._check_dict_path(event, 'transfer'):
            if event['transfer']['from'] == self.entity_public_key:
                tokens = event['transfer']['amount']
                destination = event['transfer']['to']

                logger.debug('%s Node %s transfered %s tokens at height %s ' +
                             'to %s', self, self.name, tokens, event_height,
                             event['transfer']['to'])
                channels.alert_info(TokensTransferedToAlert(
                    self.name,
                    tokens,
                    event_height,
                    destination))

            elif event['transfer']['to'] == self.entity_public_key:
                tokens = event['transfer']['amount']
                source = event['transfer']['from']

                logger.debug('%s Node %s transfered %s tokens at height %s ' +
                             'from, %s', self, self.name, tokens, event_height,
                             event['transfer']['to'])
                channels.alert_info(TokensTransferedFromAlert(
                    self.name,
                    tokens,
                    event_height,
                    source))

        elif self._check_dict_path(event, 'allowance_change'):
            if event['allowance_change']['owner'] == self.entity_public_key:
                beneficiary = event['allowance_change']['beneficiary']
                new_allowance = event['allowance_change']['allowance']
                amount_change = event['allowance_change']['amount_change']
                reduced = event['allowance_change']['negative']
                            
                logger.info('%s Node %s allowance_change %s tokens at height %s.  New allowance %s, reduced: %s, beneficiary: %s', 
                              self, self.name, amount_change, event_height, new_allowance, reduced, beneficiary)
                channels.alert_critical(AllowanceChangeAlert(
                    self.name,
                    amount_change,
                    reduced,
                    beneficiary,
                    new_allowance,
                    event_height))
        else:
            logger.debug('%s Node %s received unknown event : %s', self, self.name,
                         event)
            channels.alert_warning(UnknownEventFound(
                self.name,
                event_height,
                event))

    def disconnect_from_api(self, channels: ChannelSet, logger: logging.Logger):
        logger.debug('%s disconnect_from_api: channels=%s', self, channels)

        if self.is_connected_to_api_server:
            if self.is_validator:
                channels.alert_critical(
                    NodeWasNotConnectedToApiServerAlert(self.name))
            else:
                channels.alert_warning(
                    NodeWasNotConnectedToApiServerAlert(self.name))

        self._connected_to_api_server = False

    def connect_with_api(self, channels: ChannelSet, logger: logging.Logger):
        logger.debug('%s connect_with_api: channels=%s', self, channels)

        if not self.is_connected_to_api_server:
            channels.alert_info(NodeConnectedToApiServerAgainAlert(self.name))

        self._connected_to_api_server = True

    # Funciton to check if a path in a dictionray exists
    def _check_dict_path(self, d: dict, *indices: str) -> bool:
        sentinel = object()
        for index in indices:
            d = d.get(index, sentinel)
            if d is sentinel:
                return False
        return True
