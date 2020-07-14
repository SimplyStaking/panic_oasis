class System {
  constructor(name, chain, systemHasValidator, processCPUSecondsTotal,
    processMemoryUsage, virtualMemoryUsage, openFileDescriptors, systemCPUUsage,
    systemRAMUsage, systemStorageUsage) {
    this.name_ = name || '';
    this.chain_ = chain || '';
    this.systemHasValidator_ = systemHasValidator || false;
    this.processCPUSecondsTotal_ = processCPUSecondsTotal || 0;
    this.processMemoryUsage_ = processMemoryUsage || 0;
    this.virtualMemoryUsage_ = virtualMemoryUsage || 0;
    this.openFileDescriptors_ = openFileDescriptors || 0;
    this.systemCPUUsage_ = systemCPUUsage || 0;
    this.systemRAMUsage_ = systemRAMUsage || 0;
    this.systemStorageUsage_ = systemStorageUsage || 0;
  }

  get name() {
    return this.name_;
  }

  get chain() {
    return this.chain_;
  }

  get systemHasValidator() {
    return this.systemHasValidator_;
  }

  get processCPUSecondsTotal() {
    return this.processCPUSecondsTotal_;
  }

  get processMemoryUsage() {
    return this.processMemoryUsage_;
  }

  get virtualMemoryUsage() {
    return this.virtualMemoryUsage_;
  }

  get openFileDescriptors() {
    return this.openFileDescriptors_;
  }

  get systemCPUUsage() {
    return this.systemCPUUsage_;
  }

  get systemRAMUsage() {
    return this.systemRAMUsage_;
  }

  get systemStorageUsage() {
    return this.systemStorageUsage_;
  }
}

export default System;
