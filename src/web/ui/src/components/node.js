class Node {
  constructor(name, chain, isValidator, wentDownAt, isDown, isSyncing,
    noOfPeers, lastHeightUpdate, height, bondedBalance, isActive,
    isMissingBlocks, debondingBalance, sharesBalance, votingPower,
    consecutiveBlocksMissed) {
    
    this.name_ = name || '';
    this.chain_ = chain || '';
    this.isValidator_ = isValidator || false;
    this.wentDownAt_ = wentDownAt || null;
    this.isDown_ = isDown || false;
    this.isSyncing_ = isSyncing || false;
    this.noOfPeers_ = noOfPeers || 0;
    this.lastHeightUpdate_ = lastHeightUpdate || Date.now(); // timestamp
    this.height_ = height || 0;
    this.bondedBalance_ = bondedBalance || 0;
    this.debondingBalance_ = debondingBalance || 0;
    this.sharesBalance_ = sharesBalance || 0;
    this.votingPower_ = votingPower || 0;
    this.isActive_ = isActive || false;
    this.isMissingBlocks_ = isMissingBlocks || false;
    this.consecutiveBlocksMissed_ = consecutiveBlocksMissed || 0;
  }

  get name() {
    return this.name_;
  }

  get chain() {
    return this.chain_;
  }

  get isValidator() {
    return this.isValidator_;
  }

  get wentDownAt() {
    return this.wentDownAt_;
  }

  get isDown() {
    return this.isDown_;
  }

  get isSyncing() {
    return this.isSyncing_;
  }

  get noOfPeers() {
    return this.noOfPeers_;
  }

  get lastHeightUpdate() {
    return this.lastHeightUpdate_;
  }

  get height() {
    return this.height_;
  }

  get bondedBalance() {
    return this.bondedBalance_;
  }

  get debondingBalance() {
    return this.debondingBalance_;
  }

  get sharesBalance() {
    return this.sharesBalance_;
  }

  get votingPower() {
    return this.votingPower_;
  }

  get isActive() {
    return this.isActive_;
  }

  get isMissingBlocks() {
    // if (this.consecutiveBlocksMissed_ > 0){
    //   return true;
    // }else{
    //   return false;
    // }
    return this.isMissingBlocks_;
  }

  get consecutiveBlocksMissed() {
    return this.consecutiveBlocksMissed_;
  }
}

export default Node;
