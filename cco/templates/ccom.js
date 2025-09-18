// CCOM v0.2 - Memory System with Management Features (400 lines total)
const fs = require('fs');
const path = require('path');

class CCOM {
  constructor() {
    this.memoryPath = path.join(__dirname, 'memory.json');
    this.archivePath = path.join(__dirname, 'archive');
    this.memory = this.loadMemory();
    this.setupHooks();
  }

  // Core memory functions
  loadMemory() {
    try {
      const data = fs.readFileSync(this.memoryPath, 'utf8');
      return JSON.parse(data);
    } catch (e) {
      // First run or corrupted - create new
      const empty = this.createEmptyMemory();
      this.saveMemory(empty);
      return empty;
    }
  }

  saveMemory(memory = this.memory) {
    try {
      fs.writeFileSync(this.memoryPath, JSON.stringify(memory, null, 2));
      this.memory = memory;
      return true;
    } catch (e) {
      console.error('Failed to save memory:', e.message);
      return false;
    }
  }

  createEmptyMemory() {
    return {
      project: {
        name: path.basename(process.cwd()),
        created: new Date().toISOString().split('T')[0]
      },
      features: {},
      metadata: {
        version: '0.2',
        created: new Date().toISOString(),
        lastCleanup: new Date().toISOString()
      }
    };
  }

  // Feature management
  rememberFeature(name, data = {}) {
    // Check for exact duplicate
    if (this.checkDuplicate(name)) {
      console.log(`⚠️  Duplicate detected: "${name}" already exists!`);
      return false;
    }

    this.memory.features[name] = {
      created: new Date().toISOString(),
      description: data.description || '',
      files: data.files || [],
      userTerm: data.userTerm || name
    };

    this.saveMemory();
    console.log(`✅ Remembered: ${name}`);
    return true;
  }

  checkDuplicate(name) {
    const normalized = name.toLowerCase().trim();

    for (const existing of Object.keys(this.memory.features)) {
      if (existing.toLowerCase().trim() === normalized) {
        return existing;
      }

      // Also check user terms
      const feature = this.memory.features[existing];
      if (feature.userTerm && feature.userTerm.toLowerCase().trim() === normalized) {
        return existing;
      }
    }

    return false;
  }

  // Memory Management Features (v0.2)
  getMemoryStats() {
    const features = this.memory.features;
    const featureCount = Object.keys(features).length;
    const memoryStr = JSON.stringify(this.memory);
    const bytes = Buffer.byteLength(memoryStr, 'utf8');
    const tokens = Math.ceil(bytes / 4); // Approximate tokens
    const percentage = (tokens / 200000) * 100; // Claude's 200k context

    // Get oldest and newest features
    const dates = Object.values(features).map(f => new Date(f.created));
    const oldest = dates.length > 0 ? new Date(Math.min(...dates)) : null;
    const newest = dates.length > 0 ? new Date(Math.max(...dates)) : null;

    return {
      featureCount,
      bytes,
      tokens,
      percentage,
      oldest: oldest ? oldest.toISOString().split('T')[0] : null,
      newest: newest ? newest.toISOString().split('T')[0] : null,
      version: this.memory.metadata?.version || '0.1'
    };
  }

  getOldestFeature() {
    const features = this.memory.features;
    if (Object.keys(features).length === 0) return null;

    let oldest = null;
    let oldestDate = null;

    for (const [name, data] of Object.entries(features)) {
      const date = new Date(data.created);
      if (!oldestDate || date < oldestDate) {
        oldestDate = date;
        oldest = { name, ...data };
      }
    }

    return oldest;
  }

  getNewestFeature() {
    const features = this.memory.features;
    if (Object.keys(features).length === 0) return null;

    let newest = null;
    let newestDate = null;

    for (const [name, data] of Object.entries(features)) {
      const date = new Date(data.created);
      if (!newestDate || date > newestDate) {
        newestDate = date;
        newest = { name, ...data };
      }
    }

    return newest;
  }

  archiveOldFeatures(days = 30) {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - days);

    const toArchive = [];
    const features = this.memory.features;

    for (const [name, data] of Object.entries(features)) {
      const featureDate = new Date(data.created);
      if (featureDate < cutoffDate) {
        toArchive.push({ name, ...data });
      }
    }

    if (toArchive.length === 0) {
      console.log('📁 No features older than ' + days + ' days found');
      return 0;
    }

    // Create archive file
    const archiveFile = path.join(this.archivePath, `archive-${new Date().toISOString().split('T')[0]}.json`);
    const archiveData = {
      archivedDate: new Date().toISOString(),
      cutoffDays: days,
      features: {}
    };

    // Move features to archive
    for (const feature of toArchive) {
      archiveData.features[feature.name] = {
        created: feature.created,
        description: feature.description,
        files: feature.files,
        userTerm: feature.userTerm
      };
      delete this.memory.features[feature.name];
    }

    // Save archive
    try {
      if (!fs.existsSync(this.archivePath)) {
        fs.mkdirSync(this.archivePath, { recursive: true });
      }
      fs.writeFileSync(archiveFile, JSON.stringify(archiveData, null, 2));

      // Update metadata
      if (!this.memory.metadata) this.memory.metadata = {};
      this.memory.metadata.lastCleanup = new Date().toISOString();

      this.saveMemory();
      console.log(`📁 Archived ${toArchive.length} features older than ${days} days to ${path.basename(archiveFile)}`);
      return toArchive.length;
    } catch (e) {
      console.error('Failed to create archive:', e.message);
      return 0;
    }
  }

  removeFeature(name) {
    const normalized = name.toLowerCase().trim();

    for (const existing of Object.keys(this.memory.features)) {
      if (existing.toLowerCase().trim() === normalized) {
        delete this.memory.features[existing];
        this.saveMemory();
        console.log(`🗑️ Removed feature: ${existing}`);
        return true;
      }
    }

    console.log(`❌ Feature not found: ${name}`);
    return false;
  }

  compactMemory() {
    let compacted = 0;
    const maxDescLength = 100;

    for (const [name, data] of Object.entries(this.memory.features)) {
      if (data.description && data.description.length > maxDescLength) {
        const original = data.description;
        data.description = data.description.substring(0, maxDescLength - 3) + '...';
        compacted++;
        console.log(`✂️ Truncated description for "${name}"`);
        console.log(`   From: ${original}`);
        console.log(`   To: ${data.description}`);
      }
    }

    if (compacted > 0) {
      this.saveMemory();
      console.log(`🗜️ Compacted ${compacted} feature descriptions`);
    } else {
      console.log('✅ No descriptions need compacting');
    }

    return compacted;
  }

  listFeatures(sortBy = 'created') {
    const features = Object.entries(this.memory.features);

    if (features.length === 0) {
      console.log('📭 No features remembered yet');
      return;
    }

    // Sort features
    features.sort((a, b) => {
      const [nameA, dataA] = a;
      const [nameB, dataB] = b;

      switch (sortBy) {
        case 'name':
          return nameA.localeCompare(nameB);
        case 'created':
        default:
          return new Date(dataA.created) - new Date(dataB.created);
      }
    });

    console.log('\n📋 Feature List');
    console.log('━'.repeat(60));

    for (const [name, data] of features) {
      const created = new Date(data.created);
      const age = Math.floor((new Date() - created) / (1000 * 60 * 60 * 24));
      const ageStr = age === 0 ? 'today' : age === 1 ? '1 day ago' : `${age} days ago`;

      console.log(`\n  📦 ${name}`);
      if (data.userTerm && data.userTerm !== name) {
        console.log(`      Alias: "${data.userTerm}"`);
      }
      if (data.description) {
        console.log(`      Description: ${data.description}`);
      }
      if (data.files && data.files.length > 0) {
        console.log(`      Files: ${data.files.join(', ')}`);
      }
      console.log(`      Created: ${created.toISOString().split('T')[0]} (${ageStr})`);
    }
    console.log('━'.repeat(60));
  }

  displayMemoryStats() {
    const stats = this.getMemoryStats();

    console.log('\n📊 Memory Statistics');
    console.log('━'.repeat(40));
    console.log(`Version: ${stats.version}`);
    console.log(`Features: ${stats.featureCount}`);
    console.log(`Memory size: ${stats.bytes} bytes (${stats.tokens} tokens)`);
    console.log(`Context usage: ${stats.percentage.toFixed(2)}%`);

    if (stats.oldest) {
      console.log(`Oldest feature: ${stats.oldest}`);
    }
    if (stats.newest) {
      console.log(`Newest feature: ${stats.newest}`);
    }

    // Warning thresholds
    if (stats.tokens > 20000) {
      console.log('🚨 CRITICAL: Memory usage > 10% of context! Archive immediately!');
    } else if (stats.tokens > 10000) {
      console.log('⚠️ WARNING: Memory usage > 5% of context. Consider archiving.');
    } else if (stats.tokens > 5000) {
      console.log('💡 INFO: Memory usage > 2.5% of context. Monitor growth.');
    }

    console.log('━'.repeat(40));
    return stats;
  }

  // Context injection for Claude
  getContextSummary() {
    const featureCount = Object.keys(this.memory.features).length;
    const stats = this.getMemoryStats();

    if (featureCount === 0) {
      return `Starting fresh project: ${this.memory.project.name}`;
    }

    const features = Object.entries(this.memory.features)
      .map(([name, data]) => {
        const userTerm = data.userTerm !== name ? ` (aka "${data.userTerm}")` : '';
        return `• ${name}${userTerm}: ${data.description || 'No description'}`;
      })
      .join('\n');

    let warning = '';
    if (stats.tokens > 10000) {
      warning = '\n🚨 Memory usage high - consider archiving old features!';
    } else if (stats.tokens > 5000) {
      warning = '\n💡 Memory usage moderate - monitor growth';
    }

    return `
🧠 Memory Loaded: ${this.memory.project.name} (v${stats.version})
Memory: ${stats.tokens} tokens (${stats.percentage.toFixed(1)}% of context)
Features built (${featureCount}):
${features}

⚠️ Check for duplicates before creating new features!${warning}
    `.trim();
  }

  // Display functions
  showMemory() {
    console.log('\n📝 Memory Contents');
    console.log('━'.repeat(40));
    console.log(`Project: ${this.memory.project.name}`);
    console.log(`Created: ${this.memory.project.created}`);
    console.log(`\nFeatures (${Object.keys(this.memory.features).length}):`);

    for (const [name, data] of Object.entries(this.memory.features)) {
      console.log(`\n  ${name}`);
      if (data.userTerm && data.userTerm !== name) {
        console.log(`    Alias: "${data.userTerm}"`);
      }
      if (data.description) {
        console.log(`    Description: ${data.description}`);
      }
      if (data.files && data.files.length > 0) {
        console.log(`    Files: ${data.files.join(', ')}`);
      }
      console.log(`    Created: ${data.created}`);
    }
    console.log('━'.repeat(40));
  }

  clearMemory() {
    const empty = this.createEmptyMemory();
    this.saveMemory(empty);
    console.log('✅ Memory cleared');
  }

  // Hook setup for Claude Code integration
  setupHooks() {
    // This would integrate with Claude Code's hook system
    // For v0.1, we just provide the methods

    // On session start
    this.onSessionStart = () => {
      const context = this.getContextSummary();
      console.log(context);
      return context;
    };

    // On command received
    this.onCommand = (command) => {
      const lower = command.toLowerCase();

      // Check for memory commands
      if (lower.includes('remember this as')) {
        const match = command.match(/remember this as[:\s]+(.+)/i);
        if (match) {
          this.rememberFeature(match[1].trim());
        }
      } else if (lower.includes('what have we built') || lower.includes('show memory')) {
        this.showMemory();
      } else if (lower.includes('clear memory')) {
        this.clearMemory();
      } else {
        // Check for duplicate creation attempts
        const createWords = ['create', 'add', 'build', 'make'];
        for (const word of createWords) {
          if (lower.includes(word)) {
            const possibleFeature = lower.replace(new RegExp(word, 'g'), '').trim();
            const duplicate = this.checkDuplicate(possibleFeature);
            if (duplicate) {
              console.log(`⚠️  Similar feature exists: "${duplicate}". Consider enhancing it instead.`);
            }
          }
        }
      }
    };
  }
}

// Export for use
module.exports = CCOM;

// If run directly, show status
if (require.main === module) {
  const ccom = new CCOM();

  const args = process.argv.slice(2);
  const command = args[0];

  switch(command) {
    case 'start':
      console.log(ccom.onSessionStart());
      break;
    case 'memory':
      ccom.showMemory();
      break;
    case 'clear':
      ccom.clearMemory();
      break;
    case 'remember':
      const name = args[1];
      const description = args.slice(2).join(' ');
      if (name) {
        ccom.rememberFeature(name, { description });
      } else {
        console.log('Usage: node ccom.js remember <name> [description]');
      }
      break;
    case 'stats':
      ccom.displayMemoryStats();
      break;
    case 'list':
      const sortBy = args[1] || 'created';
      ccom.listFeatures(sortBy);
      break;
    case 'archive':
      const days = parseInt(args[1]) || 30;
      ccom.archiveOldFeatures(days);
      break;
    case 'remove':
      const featureName = args.slice(1).join(' ');
      if (featureName) {
        ccom.removeFeature(featureName);
      } else {
        console.log('Usage: node ccom.js remove <feature-name>');
      }
      break;
    case 'compact':
      ccom.compactMemory();
      break;
    default:
      console.log(`
CCOM v0.2 - Memory System with Management Features

Core Commands:
  node ccom.js start              - Show context summary & load memory
  node ccom.js remember <name> [description] - Remember a feature
  node ccom.js memory             - Display all remembered features
  node ccom.js clear              - Clear memory (start fresh)

Memory Management:
  node ccom.js stats              - Show memory usage statistics
  node ccom.js list [sort]        - List features (sort: created|name)
  node ccom.js archive [days]     - Archive features older than N days (default: 30)
  node ccom.js remove <name>      - Delete specific feature
  node ccom.js compact            - Truncate long descriptions to save space

Memory Limits:
  Warning: 5,000 tokens (2.5% of context)
  Archive: 10,000 tokens (5% of context)
  Maximum: 20,000 tokens (10% of context)
      `);
  }
}