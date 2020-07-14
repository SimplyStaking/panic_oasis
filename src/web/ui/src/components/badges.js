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
      if (node.isMissingBlocks == true) {
        if (node.consecutiveBlocksMissed <= 2) {
          isMissingBlocksBadge = createBadge('Missing Blocks', 'warning', 'Missing Blocks');
        } else {
          isMissingBlocksBadge = createBadge('Missing Blocks', 'danger', 'Missing Blocks');
        }
      } else {
        isMissingBlocksBadge = createBadge('Not Missing Blocks', 'success', 'Not Missing Blocks');
      }
    }
    badges.push(activeBadge, isMissingBlocksBadge);
  }
  return badges;
}

function SystemBadges({ system, activeChainJson, systemHasValidator }) {
  let processMemoryUsageBadge = null;
  let openFileDescriptorsBadge = null;
  let systemCPUUsageBadge = null;
  let systemRamUsageBadge = null;
  let systemStorageUsageBadge = null;
  const { systemBoundaries } = activeChainJson;
  const configPreFix = systemHasValidator ? 'validator_' : 'node_';
  const processMemoryUsageDanger = parseInt(systemBoundaries[
    `${configPreFix}process_memory_usage_danger_boundary`
  ], 10);
  const processMemoryUsageSafe = parseInt(systemBoundaries[
    `${configPreFix}process_memory_usage_safe_boundary`
  ], 10);
  const openFileDescriptorsDanger = parseInt(systemBoundaries[
    `${configPreFix}open_file_descriptors_danger_boundary`
  ], 10);
  const openFileDescriptorsSafe = parseInt(systemBoundaries[
    `${configPreFix}open_file_descriptors_safe_boundary`
  ], 10);
  const systemCPUUsageDanger = parseInt(systemBoundaries[
    `${configPreFix}system_cpu_usage_danger_boundary`
  ], 10);
  const systemCPUUsageSafe = parseInt(systemBoundaries[
    `${configPreFix}system_cpu_usage_safe_boundary`
  ], 10);
  const systemRamUsageDanger = parseInt(systemBoundaries[
    `${configPreFix}system_ram_usage_danger_boundary`
  ], 10);
  const systemRamUsageSafe = parseInt(systemBoundaries[
    `${configPreFix}system_ram_usage_safe_boundary`
  ], 10);
  const systemStorageUsageDanger = parseInt(systemBoundaries[
    `${configPreFix}system_storage_usage_danger_boundary`
  ], 10);
  const systemStorageUsageSafe = parseInt(systemBoundaries[
    `${configPreFix}system_storage_usage_safe_boundary`
  ], 10);

  if (!Number.isNaN(processMemoryUsageDanger)
    && !Number.isNaN(processMemoryUsageSafe)
    && system.processMemoryUsage !== -1) {
    if (system.processMemoryUsage >= processMemoryUsageDanger) {
      processMemoryUsageBadge = createBadge(
        'Process Memory Usage', 'danger', 'Critical Process Memory Usage',
      );
    } else if (system.processMemoryUsage <= processMemoryUsageSafe) {
      processMemoryUsageBadge = createBadge(
        'Process Memory Usage', 'success', 'Good Process Memory Usage',
      );
    } else {
      processMemoryUsageBadge = createBadge(
        'Process Memory Usage', 'warning', 'Warning Process Memory Usage',
      );
    }
  }

  if (!Number.isNaN(openFileDescriptorsDanger)
    && !Number.isNaN(openFileDescriptorsSafe)
    && system.openFileDescriptors !== -1) {
    if (system.openFileDescriptors >= openFileDescriptorsDanger) {
      openFileDescriptorsBadge = createBadge(
        'Open File Descriptors', 'danger', 'Critical Open File Descriptors',
      );
    } else if (system.openFileDescriptors <= openFileDescriptorsSafe) {
      openFileDescriptorsBadge = createBadge(
        'Open File Descriptors', 'success', 'Good Open File Descriptors',
      );
    } else {
      openFileDescriptorsBadge = createBadge(
        'Open File Descriptors', 'warning', 'Warning Open File Descriptors',
      );
    }
  }

  if (!Number.isNaN(systemCPUUsageDanger)
    && !Number.isNaN(systemCPUUsageSafe)
    && system.systemCPUUsage !== -1) {
    if (system.systemCPUUsage >= systemCPUUsageDanger) {
      systemCPUUsageBadge = createBadge(
        'System CPU Usage', 'danger', 'Critical System CPU Usage',
      );
    } else if (system.systemCPUUsage <= systemCPUUsageSafe) {
      systemCPUUsageBadge = createBadge(
        'System CPU Usage', 'success', 'Good System CPU Usage',
      );
    } else {
      systemCPUUsageBadge = createBadge(
        'System CPU Usage', 'warning', 'Warning System CPU Usage',
      );
    }
  }

  if (!Number.isNaN(systemRamUsageDanger)
    && !Number.isNaN(systemCPUUsageSafe)
    && system.systemRAMUsage !== -1) {
    if (system.systemRAMUsage >= systemCPUUsageDanger) {
      systemRamUsageBadge = createBadge(
        'System RAM Usage', 'danger', 'Critical System RAM Usage',
      );
    } else if (system.systemRAMUsage <= systemRamUsageSafe) {
      systemRamUsageBadge = createBadge(
        'System RAM Usage', 'success', 'Good System RAM Usage',
      );
    } else {
      systemRamUsageBadge = createBadge(
        'System RAM Usage', 'warning', 'Warning System RAM Usage',
      );
    }
  }

  if (!Number.isNaN(systemStorageUsageDanger)
    && !Number.isNaN(systemStorageUsageSafe)
    && system.systemStorageUsage !== -1) {
    if (system.systemStorageUsage >= systemStorageUsageDanger) {
      systemStorageUsageBadge = createBadge(
        'System Storage Usage', 'danger', 'Critical System Storage Usage',
      );
    } else if (system.systemStorageUsage <= systemStorageUsageSafe) {
      systemStorageUsageBadge = createBadge(
        'System Storage Usage', 'success', 'Good System Storage Usage',
      );
    } else {
      systemStorageUsageBadge = createBadge(
        'System Storage Usage', 'warning', 'Warning System Storage Usage',
      );
    }
  }

  return [
    processMemoryUsageBadge, openFileDescriptorsBadge, systemCPUUsageBadge,
    systemRamUsageBadge, systemStorageUsageBadge,
  ];
}

export { NodeBadges, SystemBadges };
