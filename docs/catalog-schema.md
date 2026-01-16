# Catalog Schema Documentation

**Version:** 1.0  
**Purpose:** Define the structure of `catalog.yml` - the central registry for tool sources, toolboxes, and tool assignments.

## Overview

The catalog is a YAML file that tracks:
- **Sources** - Where tools come from (Git repos, local folders, network drives)
- **Toolboxes** - ArcGIS Pro Python Toolboxes (.pyt files) that reference tools
- **Tool Mappings** - Which tools from which sources are included in which toolboxes

## File Location

**Default:** `~/.arcgis_yaml_toolbox/catalog.yml` (user's home directory)  
**Overridable:** Via environment variable `ARCGIS_YAML_CATALOG` or config file

## Schema Structure

```yaml
version: "1.0"                  # Schema version for future compatibility

# Global settings (optional)
settings:
  arcgis_pro_path: "C:/Program Files/ArcGIS/Pro"   # Auto-detected if not specified
  python_env: "arcgispro-py3"                       # Python environment name
  auto_sync: true                                   # Auto-sync Git sources on startup

# Tool sources - where tools are discovered
sources:
  - id: string                  # REQUIRED: Unique identifier (slug format)
    name: string                # REQUIRED: Human-readable name
    type: enum                  # REQUIRED: "git" | "local" | "network"
    
    # Type-specific fields
    url: string                 # For git: Repository URL
    branch: string              # For git: Branch name (default: "main")
    path: string                # For local/network: Absolute path
    
    # Management fields
    local_path: string          # Where source is stored locally (auto-generated for git)
    enabled: boolean            # Whether to scan for tools (default: true)
    last_sync: datetime         # Last successful sync/scan timestamp
    
    # Metadata (auto-populated by scanner)
    discovered_tools: int       # Number of tools found
    last_error: string          # Last error message (if any)

# Toolboxes - .pyt files that reference tools from sources
toolboxes:
  - id: string                  # REQUIRED: Unique identifier (slug format)
    name: string                # REQUIRED: Human-readable name
    description: string         # OPTIONAL: Toolbox description
    path: string                # REQUIRED: Absolute path to .pyt file
    
    # Tool assignments
    tools:
      - source_id: string       # REQUIRED: References source.id
        tool_path: string       # REQUIRED: Relative path within source (e.g., "tools/buffer_analysis")
        enabled: boolean        # OPTIONAL: Override to disable tool (default: true)
        alias: string           # OPTIONAL: Rename tool in this toolbox
    
    # Metadata
    created: datetime           # When toolbox was created
    modified: datetime          # Last modification timestamp
    auto_regenerate: boolean    # Auto-regenerate .pyt on catalog changes (default: true)
```

## Field Definitions

### Source Types

| Type | Description | Required Fields | Optional Fields |
|------|-------------|-----------------|-----------------|
| `git` | Git repository (GitHub, GitLab, etc.) | `id`, `name`, `url` | `branch`, `local_path` |
| `local` | Local folder on this machine | `id`, `name`, `path` | None |
| `network` | Network drive or UNC path | `id`, `name`, `path` | None |

### Source ID Rules
- Must be unique within catalog
- Slug format: lowercase, alphanumeric, hyphens only
- Examples: `my-hydrology-tools`, `field-tools`, `company-gis-toolkit`

### Tool Path Format
- Relative to source root
- Points to tool folder containing `tool.yml`
- Examples: `tools/buffer_analysis`, `tools/hydrology/watershed_delineation`

## Design Decisions

### Why Track Sources Separately?
**Many-to-many relationship:** One tool can be in multiple toolboxes. By tracking sources separately, we:
- Avoid duplicating tool definitions
- Enable sharing tools across projects
- Support different versions of tools (via different sources)
- Allow source-level operations (sync all, disable all)

### Why Not Store Tools Directly?
**Discovery over declaration:** Tools are discovered by scanning sources, not manually listed in the catalog. This:
- Reduces manual maintenance
- Auto-discovers new tools when sources sync
- Keeps catalog file small and manageable
- Matches Git workflow (tools live in repos, catalog just points to them)

### Why Local Path for Git Sources?
**Offline capability:** Clone Git repos to local storage so tools work offline. Users can:
- Work in the field without connectivity
- Run tools without network access
- Sync when convenient (not required for execution)

### Why Enabled Flags at Multiple Levels?
**Granular control without deletion:**
- Disable source: Temporarily hide all tools from that source
- Disable tool: Keep in toolbox definition but don't show in Pro
- Allows toggling without losing configuration

## Usage Patterns

### Adding a New Source
```yaml
sources:
  - id: team-hydrology
    name: "Team Hydrology Tools"
    type: git
    url: https://github.com/org/hydrology-tools
    # local_path, last_sync, discovered_tools auto-populated by manager
```

### Creating a Toolbox
```yaml
toolboxes:
  - id: field-analysis
    name: "Field Analysis Toolbox"
    path: C:/Projects/FieldWork/field_analysis.pyt
    tools: []  # Empty initially, tools added via manager
```

### Assigning Tools to Toolbox
```yaml
toolboxes:
  - id: field-analysis
    name: "Field Analysis Toolbox"
    path: C:/Projects/FieldWork/field_analysis.pyt
    tools:
      - source_id: team-hydrology
        tool_path: tools/watershed_delineation
      - source_id: team-hydrology
        tool_path: tools/flow_accumulation
      - source_id: local-tools
        tool_path: tools/buffer_analysis
```

### Temporarily Disabling a Tool
```yaml
tools:
  - source_id: team-hydrology
    tool_path: tools/old_analysis
    enabled: false  # Hidden from Pro but not deleted
```

## Future Considerations

**Version 1.0 (Current):**
- Single catalog file
- Manual source management
- Basic Git integration (clone/pull)

**Version 2.0 (Possible Future):**
- Tool versioning/pinning (specific commits)
- Dependency tracking between tools
- Tool usage analytics
- Multiple catalog files (project-specific catalogs)
- Remote catalog sync (team catalogs)
- Tool marketplace integration

**Breaking Changes Policy:**
- `version` field ensures forward compatibility
- New versions add fields, never remove
- Old managers ignore unknown fields (forward-compatible)
- New managers support old schemas (backward-compatible)

## Validation Rules

1. **Unique IDs:** All `id` fields must be unique within their scope (sources, toolboxes)
2. **Valid Paths:** All `path` fields must be valid filesystem paths
3. **Valid References:** All `source_id` in tool assignments must reference existing sources
4. **Valid URLs:** Git source `url` must be valid Git repository URL
5. **Tool Path Existence:** `tool_path` should exist when source is synced (warning, not error)

## Error Handling

**Missing Sources:** If a toolbox references a source that doesn't exist:
- Log warning
- Skip those tools
- Don't break toolbox generation

**Missing Tools:** If a tool path doesn't exist in source:
- Log warning
- Skip that tool
- Don't break toolbox generation
- User can remove from catalog when convenient

**Invalid YAML:** If catalog is corrupted:
- Attempt to load with error recovery
- Create backup before any writes
- Provide clear error messages with line numbers

## Security Considerations

**Git Sources:**
- Never auto-execute code from Git repos without user confirmation
- Scan for malicious patterns before loading tools
- Display Git URL clearly before cloning

**Network Paths:**
- Validate UNC paths before accessing
- Handle access denied gracefully
- Don't store credentials (use OS-level auth)

**Local Paths:**
- Validate paths are within expected directories
- Warn if pointing to system directories
- Use absolute paths only (prevent path traversal)
