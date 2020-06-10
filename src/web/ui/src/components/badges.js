import { createBadge } from '../utils/dashboard';

function NodeBadges({ node }) {
  let syncingBadge = null;
  let activeBadge = null;
  let isMissingBlocksBadge = null;
  
  if (node.isSyncing !== -1) {
    syncingBadge = node.isSyncing
      ? createBadge('Syncing', 'warning', 'Syncing')
      : createBadge('Synced', 'success', 'Synced');
  }

  const badges = [
    node.isDown ? createBadge('Down', 'danger', 'Down')
      : createBadge('Up', 'success', 'Up'),
    syncingBadge,
  ];
  if (node.isValidator) {
    if (node.isActive !== -1) {
      activeBadge = node.isActive ? createBadge('Active', 'success', 'Active')
        : createBadge('Inactive', 'danger', 'Inactive');
    }
    if (node.isMissingBlocks !== -1) {
      if (node.isMissingBlocks == true){
        if (node.consecutiveBlocksMissed <= 2 ){
          isMissingBlocksBadge = createBadge('Missing Blocks', 'warning', 'Missing Blocks');
        }else{
          isMissingBlocksBadge = createBadge('Missing Blocks', 'danger', 'Missing Blocks');
        }
      }else{
        isMissingBlocksBadge = createBadge('Not Missing Blocks', 'success', 'Not Missing Blocks');
      }
    }
    badges.push(activeBadge, isMissingBlocksBadge);
  }
  return badges;
}

export default NodeBadges;
