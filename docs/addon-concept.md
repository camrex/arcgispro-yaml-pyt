# ArcGIS Pro Add-in Concept

**Status:** Conceptual sketch (not yet implemented)  
**Date:** January 15, 2026

## Vision

An ArcGIS Pro Add-in that makes building and managing GIS tools as easy as saving documents. The Add-in provides the framework engine while users maintain simple Git repositories containing only YAML configs and Python business logic.

### Core Value Proposition

**"Never lose a tool again. Find any tool you've ever written, instantly."**

**Standalone Framework:**
- Build tools in YAML (no boilerplate)
- Bundle framework with toolbox (no dependencies)
- Share via any method (Git, zip, network drive)
- Works anywhere ArcGIS Pro works

**Add-in Superpowers:**
- **Central tool repository** - All your tools, one searchable location
- **VCS integration** - Auto-sync with GitHub/GitLab/etc.
- **Cross-machine sync** - work → home → field laptop stays synchronized
- **Discovery** - No more hunting through old project folders for "that buffer tool I wrote 6 months ago"

**Not trying to build an ecosystem** - solving personal tool organization and the "I know I wrote that tool somewhere" problem. If sharing emerges organically, great. If not, still solves the core problem.

## Architecture

### Two Deployment Models

**Model 1: Standalone (Framework Bundled)**
- Framework code included in each toolbox repository
- Completely self-contained, zero external dependencies
- Share via zip, Git, network drive - works anywhere
- Users control framework version

**Model 2: Add-in (Tool Catalog Manager)**
- Framework lives in Add-in (single installation)
- **Central tool catalog** - All available tools from all sources
- **Tool assignment** - Compose toolboxes from catalog (many-to-many)
- **Source management** - VCS repos, local folders, network drives
- **YAML-driven, UI-managed** - Add-in writes YAML, you work in UI
- Multiple toolboxes, single framework version

Both use identical YAML + Python architecture. Only difference is where framework code lives.

### Framework Stability Guarantee

**The framework is just the plumbing - it doesn't break your tools.**

**Framework's job (stable):**
- Load YAML configurations
- Discover tools in directories
- Register tools with ArcGIS Pro
- Pass parameters to your execute functions

**Your tool's job (you control):**
- Business logic (buffer, clip, analyze, etc.)
- Algorithm implementation
- Error handling
- Results formatting

**Add-in features (additive, non-breaking):**
- **Tool catalog** - Central registry of all available tools
- **Source management** - Add tools from VCS, local, network drives
- **Toolbox assignment** - Same tool in multiple toolboxes
- VCS integration (automatic sync)
- Dependency validation (warnings only)
- Tool discovery UI (search across all sources)
- Usage analytics (optional tracking)
- **YAML management** - Add-in writes/updates YAML, never manual editing

**Result:** Update the framework or add-in without fear. Your tools keep working because they only depend on the stable plumbing layer (YAML config → execute function). The framework doesn't care what your execute function does.

### Framework in Add-in, Tools in Repository

**Core principle:** Add-in provides framework. Repositories contain only tool definitions (YAML + Python logic).

#### Add-in Package (Required)

```
ArcGIS Pro Add-in:
  arcgis_yaml_toolbox/
    ├─ framework/                    # Framework engine
    │   ├─ factory.py                # Dynamic tool generation
    │   ├─ loader.py                 # Tool loading
    │   ├─ base/
    │   │   └─ yaml_tool.py          # Base tool class
    │   ├─ config/
    │   │   └─ schema.py             # Pydantic validation
    │   └─ metadata/
    │       └─ generator.py          # XML metadata generation
    │
    ├─ ui/                           # ArcGIS Pro UI integration
    │   ├─ catalog.py                # Tool browser panel
    │   ├─ repository.py             # Repository management
    │   └─ sync.py                   # Optional Git integration
    │
    └─ templates/
        ├─ toolbox_template/         # New toolbox template
        ├─ tool.yml.template         # New tool template
        └─ execute.py.template       # Execute function template

**Installed once, provides framework for all toolboxes.**
```

#### User's Toolbox Repository (Clean, No Framework Code)

```
# Can be local folder, Git repo, or any VCS
my-gis-toolbox/
  ├─ tools/                          # Each tool in its own folder
  │   ├─ buffer_analysis/
  │   │   ├─ tool.yml                # Tool configuration
  │   │   ├─ execute.py              # Main logic
  │   │   └─ helpers.py              # Optional tool-specific helpers
  │   │
  │   ├─ clip_features/
  │   │   ├─ tool.yml
  │   │   └─ execute.py
  │   │
  │   ├─ watershed_delineation/
  │   │   ├─ tool.yml
  │   │   └─ execute.py
  │   │
  │   └─ legacy_hydrology/           # Legacy .pyt tool (optional)
  │       ├─ tool.yml                # Minimal config for discovery
  │       └─ legacy.pyt              # Full .pyt or stripped .py
  │
  ├─ yaml_toolbox.pyt                # Generated by Add-in
  ├─ .toolbox_manifest.yml           # Generated by Add-in
  └─ README.md

**No framework code.** Just YAML configs + Python logic.
Git is optional - can be local folder, network drive, SharePoint, etc.
```

#### Generated .pyt File (Links to Add-in Framework)

```python
# yaml_toolbox.pyt (auto-generated by Add-in)
"""
YAML-based Python Toolbox
Managed by ArcGIS YAML Toolbox Add-in

DO NOT EDIT - Regenerate via Add-in
"""

try:
    from arcgis_yaml_toolbox.framework import ToolboxLoader
except ImportError:
    raise ImportError(
        "ArcGIS YAML Toolbox Add-in required. "
        "Install from ArcGIS Pro Add-in Manager."
    )

# Load tools from this directory
_loader = ToolboxLoader(Path(__file__).parent)
_toolbox_config, _tool_classes = _loader.load_tools()

# Export for ArcGIS Pro
for tool_class in _tool_classes:
    globals()[tool_class.__name__] = tool_class

class Toolbox:
    def __init__(self):
        self.label = _toolbox_config.label
        self.tools = _tool_classes
```

**Key benefits:**
- All toolboxes use same framework version (no fragmentation)
- Framework updates via Add-in updates (tested, controlled)
- Repositories stay clean (only user code)
- Consistent behavior across all tools

## User Workflows

### First Time Setup (Add-in Mode)

**Step 1: Install Add-in**
1. Open ArcGIS Pro
2. Add-in Manager → Install "YAML Toolbox Framework"
3. Framework and Tool Catalog Manager now available

**Step 2: Add Your First Tool Source**
1. Open "YAML Toolbox Manager" panel
2. Click "Sources" tab → "Add Source"
3. Choose source type:
   - **GitHub/GitLab** - Enter repo URL, Add-in clones automatically
   - **Local Folder** - Browse to existing tool folder
   - **Network Drive** - Point to shared tools location
4. Add-in scans for tools and populates catalog
5. Tools appear in "Catalog" browser

**Step 3: Create Your First Toolbox**
1. Click "Toolboxes" tab → "New Toolbox"
2. Name: "My Analysis Tools"
3. Location: Choose project folder
4. Add-in generates `toolbox.yml` and `.pyt` file
5. Toolbox appears in Pro (empty)

**Step 4: Assign Tools to Toolbox**
1. Open "My Analysis Tools" in Add-in
2. Click "Add Tool" → Browse catalog
3. Select tools to include (multi-select supported)
4. Click "Add to Toolbox"
5. Add-in updates `toolbox.yml`, refreshes Pro
6. Tools appear in ArcGIS Pro catalog

**Result:** Project toolbox with tools from your catalog sources. Same tools can be used in other toolboxes.

**Field/Offline Usage:**
- Tools run from local directory on your machine
- VCS sync happens when you have connectivity
- Sync before going to field → all tools available offline
- No connectivity required for tool execution (it's just Python code)

### Adding a New Tool

**Standalone Mode (Manual):**
1. Create `tools/my_tool/` folder
2. Create `tools/my_tool/tool.yml` (tool config)
3. Create `tools/my_tool/execute.py` (execute function)
4. Refresh toolbox in Catalog (Ctrl+R)
5. Tool appears in toolbox

**Standalone Mode (Legacy Tool):**
1. Create `tools/legacy_tool/` folder
2. Copy existing `.pyt` file (no modifications needed)
3. Create minimal `tools/legacy_tool/tool.yml`:
   ```yaml
   tool:
     name: legacy_tool
     label: "My Legacy Tool"
   implementation:
     type: legacy
     classPath: "tools.legacy_tool.legacy.MyToolClass"
   ```
4. Refresh toolbox in Catalog
5. Legacy tool appears alongside YAML tools

**Add-in Mode (Via UI):**
1. Open "YAML Toolbox Manager" panel
2. Select target toolbox repository
3. Click "New Tool" button
4. Fill form (name, label, category, parameters)
5. Click "Create"
6. Add-in generates:
   - `tools/my_tool/` folder
   - `tools/my_tool/tool.yml` (config)
   - `tools/my_tool/execute.py` (template with execute function)
7. Auto-commits to VCS (if configured)
8. Opens files in editor for customization
9. Tool appears immediately (file watcher triggers refresh)

**Add-in Mode (Manual - Advanced):**
1. Create `tools/my_tool/` folder manually
2. Create `tool.yml` and `execute.py` manually  
3. Add-in detects new files via file watcher
4. Prompts: "New tool detected. Enable?"
5. User clicks "Yes" → auto-commits (if VCS configured)
6. Tool appears in toolbox

**This is the current implementation.** Already works standalone.

```python
# Current standalone approach (Phase 0)
_loader = ToolboxLoader(Path(__file__).parent)
_toolbox_config, _tool_classes = _loader.load_tools()

# Export tools for Pro discovery
for tool_class in _tool_classes:
    globals()[tool_class.__name__] = tool_class

class Toolbox:
    def __init__(self):
        self.label = _toolbox_config.toolbox.label
        self.tools = [tool_class for tool_class in _tool_classes]
```

**Path-specific .pyt generation:**
- **Standalone:** Import from bundled framework (`from src.framework import ...`)
- **Add-in:** Import from Add-in framework (`from arcgis_yaml_toolbox.framework import ...`)
- Add-in can generate either version depending on user preference

### 3. Dependency Management

**Check, don't install (v1.0):**

```yaml
# In tool YAML
dependencies:
  python_packages:
    - scipy>=1.10
    - pandas>=2.0
  arcgis_extensions:
    - Spatial Analyst
```

**Add-in behavior (convenience feature, non-breaking):**
- Scans AGP conda environment on tool open
- Shows clear warnings if missing dependencies
- Provides install commands (copy-paste ready)
- User installs manually (full control)
- Tool still appears in toolbox (doesn't hide it)
- If user runs anyway, tool's own error handling takes over

**Philosophy:** Validate and warn, don't block or auto-install. You're the expert on your Python environment.

**Future (v2.0+):** Could add "Install for me" button if there's demand.

### 4. Repository Discovery

**Auto-discover tools in repo:**
```python
# Scan for all .yml files in tools/ directory
for yml_file in Path("tools").glob("**/*.yml"):
    # Load and validate tool config
    # Add to available tools list
```

**Manifest controls what's enabled:**
```yaml
# .toolbox_manifest.yml (auto-generated by Add-in)
enabled_tools:
  - tools/buffer_analysis/tool.yml
  - tools/clip_features/tool.yml
  # watershed_delineation exists but disabled
```

### 5. Tool Organization Pattern

**One folder per tool (recommended):**
```
tools/
  buffer_analysis/
    tool.yml              # Tool configuration
    execute.py            # Main execution logic
    helpers.py            # Tool-specific helpers (optional)
    __init__.py           # Optional
```

**Benefits:**
- Self-contained - everything for a tool in one place
- Easy to share - copy folder → tool moves
- Clear ownership - no wondering "which tool uses this helper?"
- Git friendly - tool changes isolated to one directory
- Delete friendly - remove tool → delete folder

**For tool suites/chains (advanced):**
```
tools/
  watershed_suite/           # Multiple related tools
    delineate/
      tool.yml
      execute.py
    calculate_stats/
      tool.yml
      execute.py
    generate_report/
      tool.yml
      execute.py
    shared/                  # Shared within suite only
      watershed_helpers.py
      validation.py
```

**Discovery:**
- Framework scans `tools/**/*tool.yml`
- Each tool folder is self-describing
- No central registry of files needed (optional manifest for enable/disable)

### 6. Legacy Tool Support

**Migration path for existing .pyt tools without full rewrite.**

**Three tool types supported:**

| Type | Structure | Modification | Use Case |
|------|-----------|--------------|----------|
| **YAML Tool** | `tool.yml` + `execute.py` | New tools | Full framework features, clean architecture |
| **Legacy (Full .pyt)** | `tool.yml` + `.pyt` (with Toolbox) | Zero - copy as-is | Quick migration, no code changes |
| **Legacy (Stripped)** | `tool.yml` + `.py` (Tool only) | Minimal - remove Toolbox | Clean up, but keep existing tool code |

**Option A: Keep full .pyt file (zero modification)**
```yaml
# tools/legacy_watershed/tool.yml
tool:
  name: legacy_watershed
  label: "Watershed Delineation (Legacy)"
  description: "Existing tool, minimal config"
  category: "Hydrology"
  
implementation:
  type: legacy                    # Signals legacy tool
  classPath: "tools.legacy_watershed.legacy.WatershedTool"
  # Framework imports .pyt and extracts just the Tool class
  # Ignores Toolbox class
```

```python
# tools/legacy_watershed/legacy.pyt (unchanged)
class Toolbox:
    def __init__(self):
        self.tools = [WatershedTool]

class WatershedTool:
    """Your existing tool code - works as-is."""
    def __init__(self):
        self.label = "Watershed Delineation"
        # ... existing code ...
    
    def getParameterInfo(self):
        # ... existing parameters ...
        pass
    
    def execute(self, parameters, messages):
        # ... existing business logic ...
        pass
```

**Option B: Stripped tool class (minimal modification)**
```yaml
# tools/legacy_watershed/tool.yml
tool:
  name: legacy_watershed
  label: "Watershed Delineation (Legacy)"
  category: "Hydrology"
  
implementation:
  type: legacy
  classPath: "tools.legacy_watershed.tool_class.WatershedTool"
```

```python
# tools/legacy_watershed/tool_class.py
# Toolbox class removed, just the tool
class WatershedTool:
    def __init__(self):
        # ... same tool code ...
```

**Framework behavior:**
```python
if config.implementation.type == "legacy":
    # Import the module
    module = import_module(config.implementation.classPath)
    
    # If .pyt file: extract tool class, ignore Toolbox
    # If .py file: use class directly
    tool_class = extract_tool_class(module, config)
else:
    # Standard YAML-driven tool: generate dynamic class
    tool_class = generate_tool_class(config)
```

**Benefits:**
- Zero or minimal modification required
- Mix legacy and YAML tools in same toolbox
- Gradual migration path (convert when ready)
- Still gets discovery/organization from Add-in
- Lower barrier to adoption

**Metadata:**
- Legacy tools use their existing getParameterInfo()
- Framework can optionally generate metadata from runtime introspection
- Or user can provide minimal metadata in YAML

### 7. Metadata Loader Tool

**Two deployment approaches:**

**Standalone Mode:**
```
tools/
  _metadata_loader/         # Convention: underscore = system tool
    tool.yml
    execute.py
```
- Just another tool in the toolbox
- Follows same folder structure as other tools
- User can remove if not needed
- Included in toolbox templates
- Regenerates XML metadata for all tools in toolbox

**Add-in Mode:**
```
Add-in UI:
  Tools Menu → "Reload All Metadata"
  Right-click tool → "Reload Metadata"
```
- Built into Add-in (not in toolbox code)
- Works across all registered toolboxes
- Bulk operations ("reload all toolboxes")
- Better UX (progress bars, error reporting, logs)
- Can detect and hide `_metadata_loader` tool from toolbox

**Hybrid approach:**
```yaml
# In tool.yml for _metadata_loader
tool:
  name: _metadata_loader
  label: "Reload Tool Metadata"
  category: "System"
  hide_in_addon: true         # Hide when Add-in detected
  
implementation:
  executeFunction: "tools._metadata_loader.execute.reload_metadata"
```

Add-in can detect system tools and hide them when it provides the same functionality.

## Add-in Architecture: Tool Catalog Manager

**The Add-in manages two distinct concerns:**

```
┌─────────────────────────────────────────────────────────────────┐
│                     Tool Catalog (Global)                       │
│  "What tools exist and where do they come from?"                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Sources:                                                       │
│    • GitHub: github.com/user/gis-tools                         │
│    • GitLab: gitlab.company.com/team/tools                     │
│    • Local:  C:/Users/user/tools/experiments                   │
│    • Network: \\server\shared\legacy-tools                      │
│                                                                 │
│  Tools (50+ available):                                         │
│    • buffer_analysis_v2      [personal_tools]                  │
│    • clip_features          [team_tools]                       │
│    • legacy_watershed       [legacy_collection]                │
│    • ...                                                        │
│                                                                 │
│  Searchable, filterable, taggable                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                      (Assign tools to)
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Project Toolboxes (Many)                      │
│  "Which tools do I want in this project?"                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Hydrology Toolbox:                  Data Management Toolbox:  │
│    • buffer_analysis_v2                • clip_features         │
│    • legacy_watershed                  • buffer_analysis_v2    │
│    • clip_features                     • ...                   │
│                                                                 │
│  Same tool can be in multiple toolboxes (references catalog)   │
└─────────────────────────────────────────────────────────────────┘
```

### 1. Tool Catalog (Your Library)

**Central registry of ALL available tools from all sources.**

```yaml
# ~/.arcgis_yaml_toolbox/catalog.yml (managed by Add-in)
catalog:
  version: "1.0.0"
  last_updated: "2026-01-16T10:30:00Z"

sources:
  - id: personal_tools
    type: vcs
    provider: github
    url: "https://github.com/user/gis-tools"
    local_path: "C:/Users/user/tools/personal"
    sync_enabled: true
    
  - id: team_tools
    type: vcs
    provider: gitlab
    url: "https://gitlab.company.com/gis/team-tools"
    local_path: "C:/Users/user/tools/team"
    sync_enabled: true
    
  - id: local_experiments
    type: local
    path: "C:/Users/user/tools/experiments"
    sync_enabled: false
    
  - id: legacy_collection
    type: network
    path: "\\\\server\\shared\\legacy-tools"
    sync_enabled: false

# Tag registry for autocomplete and suggestions
tag_registry:
  common_tags:
    - geometry
    - spatial
    - analysis
    - hydrology
    - buffer
    - clip
    - extract
    - legacy
    - preprocessing
    - vector
    - raster
  tag_usage:  # Track popularity
    geometry: 15    # Used by 15 tools
    buffer: 8
    clip: 6
    hydrology: 4

tools:
  - id: buffer_analysis_v2
    source: personal_tools
    path: "tools/buffer_analysis"
    type: yaml
    name: "buffer_analysis"
    label: "Buffer Analysis v2"
    category: "Analysis"
    tags: ["geometry", "buffer", "spatial", "vector", "preprocessing"]
    auto_tags: ["yaml-tool", "python"]  # Auto-generated
    last_synced: "2026-01-16T10:25:00Z"
    
  - id: legacy_watershed
    source: legacy_collection
    path: "hydrology/watershed.pyt"
    type: legacy
    name: "watershed_delineation"
    label: "Watershed Delineation (Legacy)"
    category: "Hydrology"
    tags: ["hydrology", "watershed", "terrain", "analysis"]
    auto_tags: ["legacy-tool", "python"]  # Auto-generated
    
  - id: clip_features
    source: team_tools
    path: "tools/clip_features"
    type: yaml
    name: "clip_features"
    label: "Clip Features"
    category: "Data Management"
    tags: ["clip", "extract", "vector", "spatial"]
    auto_tags: ["yaml-tool", "python"]
    last_synced: "2026-01-16T09:15:00Z"
```

**User operations (via Add-in UI, never manual YAML editing):**

**Add tool source:**
```
UI: Sources → Add Source → GitHub
  Enter URL: github.com/user/new-tools
  Choose local path: C:/Users/user/tools/new-tools
  Enable sync: Yes
  
Add-in:
  1. Clones repo (if VCS)
  2. Scans for tools
  3. Updates catalog.yml
  4. Tools appear in catalog browser
```

**Add individual tool from local:**
```
UI: Catalog → Add Tool → Browse Local
  Select: C:/temp/my_custom_tool/
  
Add-in:
  1. Validates tool structure
  2. Suggests tags based on:
     - Tool name/description analysis
     - Category
     - File structure
     - Similar existing tools
  3. User accepts/modifies/adds tags
  4. Copies to managed location (optional)
  5. Adds entry to catalog.yml
  6. Updates tag registry
  7. Tool appears in catalog
```

**Manage tags for existing tool:**
```
UI: Catalog → Right-click tool → Edit Tags
  Current tags: ["buffer", "spatial", "geometry"]
  
  Options:
    • Add tags (autocomplete from tag registry)
    • Remove tags
    • See popular tags
    • See suggested tags (based on category/description)
    
  Type: "vec" → Autocomplete shows: "vector" (used by 12 tools)
  Add: "vector"
  
Add-in:
  1. Updates catalog.yml
  2. Updates tag usage count
  3. Re-indexes search
```

**Sync VCS source:**
```
UI: Sources → Right-click "personal_tools" → Sync
  
Add-in:
  1. Git pull
  2. Scans for new/changed/deleted tools
  3. Updates catalog.yml
  4. Auto-tags new tools (type, source, category)
  5. Notifies: "3 tools updated, 1 new tool found"
```

**Search by tags:**
```
UI: Catalog → Search
  
  Search modes:
    • Text: "buffer analysis" → Full-text search
    • Tags: Click tag pills or type "#buffer #spatial"
    • Combined: "watershed #hydrology #legacy"
    
  Tag filtering:
    • Click "buffer" tag → Shows all 8 tools tagged "buffer"
    • Add "spatial" tag → Narrows to 5 tools (AND logic)
    • Tag cloud shows popular tags with usage counts
    
  Smart suggestions:
    • "Did you mean: #geometry (15 tools)?"
    • "Related tags: #vector, #preprocessing"
    • "Tools using 'buffer' + 'hydrology': 2 found"
    
Add-in:
  1. Real-time search as you type
  2. Tag autocomplete from registry
  3. Highlighted matches in results
  4. Sort by relevance/name/date/popularity
```

**Tag-based filtering:**
```
UI: Catalog → Filter Panel
  
  Filter by Tags:
    ☑ Show only: #geometry #spatial
    ☐ Exclude: #legacy
    
  Tag categories (expandable):
    ▸ Type: yaml-tool (35), legacy-tool (5)
    ▸ Domain: hydrology (4), geometry (15), terrain (3)
    ▸ Operation: buffer (8), clip (6), merge (4)
    ▸ Data Type: vector (25), raster (10)
    
  Popular tags (click to filter):
    • geometry (15)
    • buffer (8)
    • clip (6)
    • spatial (12)
    
Result: 8 tools match criteria
```

### 2. Toolbox Assignment (Your Projects)

**Tools from catalog are assigned to project toolboxes (many-to-many).**

```yaml
# my-project/toolbox.yml (managed by Add-in)
toolbox:
  name: hydrology_analysis
  label: "Hydrology Analysis Toolbox"
  alias: hydro
  description: "Tools for watershed and stream analysis"

assigned_tools:
  - catalog_id: buffer_analysis_v2
    enabled: true
    category_override: "Hydrology/Preprocessing"  # Optional
    
  - catalog_id: legacy_watershed
    enabled: true
    
  - catalog_id: clip_features
    enabled: true
    category_override: "Hydrology/Preprocessing"
    
  # Same tool can be in multiple toolboxes
  - catalog_id: buffer_analysis_v2
    enabled: true
    alias: "buffer_streams"  # Tool appears twice with different names
    category_override: "Hydrology/Stream Tools"
```

**User operations (via Add-in UI):**

**Assign tool to toolbox:**
```
UI: Open "Hydrology Analysis" toolbox
  → Add Tool → Browse Catalog
  → Search: "#buffer #hydrology" (tag-based search)
  → Results: 2 tools match
  → Select: "Buffer Analysis v2"
  → Add to Toolbox
  
Add-in:
  1. Adds entry to toolbox.yml
  2. Creates reference/symlink to tool in catalog
  3. Refreshes toolbox in Pro
  4. Tool appears in ArcGIS Pro catalog
  5. Toolbox inherits tool tags for discoverability
```

**Remove tool from toolbox:**
```
UI: Hydrology Toolbox → Right-click "Clip Features" → Remove
  
Add-in:
  1. Removes entry from toolbox.yml
  2. Refreshes toolbox
  3. Tool removed from Pro (but still in catalog)
```

**Same tool, multiple toolboxes:**
```
UI: Create "Data Management" toolbox
  → Add Tool → "Buffer Analysis v2" (already in Hydrology toolbox)
  → Add to Toolbox
  
Result:
  - "Buffer Analysis v2" appears in BOTH toolboxes
  - Single source, multiple assignments
  - Update tool once → updates everywhere
```

### Tagging Strategy

**Three types of tags:**

**1. User Tags (Manual)**
- Added by user via UI
- Domain-specific (e.g., "hydrology", "terrain")
- Operation-based (e.g., "buffer", "clip", "merge")
- Project-specific (e.g., "phase1", "production")

**2. Auto Tags (Generated by Add-in)**
- Tool type: `yaml-tool`, `legacy-tool`
- Source type: `github`, `local`, `network`
- Language: `python`, `r`, `javascript`
- Category-derived: Automatically from tool category

**3. Suggested Tags (AI-assisted)**
- Based on tool name/description analysis
- Similar tools comparison
- Category matching
- User can accept/reject

**Tag registry benefits:**
- Autocomplete prevents typos
- Shows popularity (usage count)
- Suggests related tags
- Maintains consistency across tools
- Enables powerful search

**Example tagging workflow:**
```
User adds new "Stream Buffer" tool:

Add-in auto-generates:
  - yaml-tool (type)
  - python (language)
  - github (if from GitHub source)
  
Add-in suggests (based on name/category):
  - buffer (used by 8 similar tools)
  - hydrology (category match)
  - stream (name analysis)
  - vector (common in category)
  
User adds:
  - watershed (project-specific)
  - preprocessing (workflow stage)
  
Final tags: [yaml-tool, python, github, buffer, hydrology, 
            stream, vector, watershed, preprocessing]
            
Search: "#buffer #hydrology" → Tool found instantly
```

### Configuration Management Flow

**User never edits YAML manually. Add-in is the configuration manager:**

```
User Action (UI)           Add-in Writes            Result
─────────────────────────────────────────────────────────────
Add VCS source       →     catalog.yml updated  →   Tools appear in catalog
Sync source          →     catalog.yml updated  →   New tools discovered
Add local tool       →     catalog.yml updated  →   Tool in catalog
Assign to toolbox    →     toolbox.yml updated  →   Tool in Pro
Remove from toolbox  →     toolbox.yml updated  →   Tool removed from Pro
Delete tool source   →     catalog.yml updated  →   Tool removed everywhere
```

### Local vs VCS Tool Handling

**VCS Tools (GitHub, GitLab, Azure DevOps):**
- Add-in clones to managed location: `~/.arcgis_yaml_toolbox/sources/{source_id}/`
- Sync button pulls latest changes
- User can edit locally, Add-in detects changes
- "Commit & Push" button syncs changes back
- Conflicts detected and presented for resolution

**Local Tools:**
- Add-in can reference in-place OR copy to managed location
- User chooses: "Reference" (stays where it is) vs "Import" (copy to managed)
- No automatic sync (user controls)
- Can "Publish to VCS" later (creates new VCS source)

**Network Tools:**
- Add-in references in-place (read-only typically)
- No sync capability
- Good for shared team tools on network drives
- Can "Import to Local" to make editable copy

**Hybrid scenarios:**
```
Started as local tool → Add-in → "Publish to GitHub"
  Add-in:
    1. Creates GitHub repo
    2. Pushes tool
    3. Converts local source to VCS source
    4. Enables sync
    
VCS tool → "Make Local Copy"
  Add-in:
    1. Creates new local source
    2. Copies tool
    3. Original VCS source unchanged
    4. Now have independent copy
```

### Benefits of This Architecture

**Separation of concerns:**
- **Catalog** = What tools exist and where they come from
- **Toolbox** = Which tools do I want in this project

**Flexibility:**
- Same tool in multiple toolboxes (no duplication)
- Mix tools from multiple sources in one toolbox
- Easy reorganization (just update assignments)

**VCS becomes transparent:**
- User thinks: "Add tool from GitHub"
- Add-in handles: clone, scan, track, sync, commit, push
- User never runs git commands

**YAML-driven but UI-managed:**
- Configuration is portable (YAML files)
- User never edits YAML manually (Add-in does it)
- Advanced users CAN edit if they want (validated on load)

**Discovery and search:**
- **Tag-based search:** `#buffer #spatial` → instant results
- **Combined search:** "watershed #hydrology #legacy" → text + tags
- **Tag cloud:** Visual popularity, click to filter
- **Smart suggestions:** Related tags, "did you mean?"
- **Tag autocomplete:** Type "#buf" → suggests "#buffer (8 tools)"
- Search across ALL sources with tag filtering
- Filter by source, type, category, tags (include/exclude)
- "I know I have that tool somewhere" → search by tag → instant find

### Architecture Comparison

| Aspect | Traditional .pyt | Standalone Framework | Add-in Catalog Manager |
|--------|-----------------|---------------------|------------------------|
| **Tool location** | Scattered across projects | One toolbox folder | Central catalog + project assignments |
| **Reuse** | Copy/paste code | Copy folder | Reference from catalog |
| **Discovery** | File search | Manual file browsing | Searchable catalog across all sources |
| **VCS** | Manual git commands | Manual git commands | Automatic sync via UI |
| **Organization** | File system only | File system + YAML config | Catalog + many-to-many assignment |
| **Multi-project** | Duplicate tools | Duplicate tools | Same tool, multiple toolboxes |
| **Configuration** | Hard-coded in .py | YAML (user edits) | YAML (Add-in manages) |

## User Workflows with Tool Catalog

**Start Simple (Standalone):**
1. Download template repository
2. Add your first tool:
   - Create `tools/my_tool/` folder
   - Add `tool.yml` (config)
   - Add `execute.py` (logic)
3. Add toolbox to Pro
4. It just works

**Migrate Legacy Tools (Optional):**
- Have existing .pyt tools?
- Create `tools/legacy_tool/` folder
- Copy `.pyt` file (no modification needed)
- Add minimal `tool.yml` pointing to it
- Legacy tool now in your new toolbox
- Migrate to full YAML when ready

**Scale Up (Add Add-in when needed):**
- You now have 10 tools across 3 projects
- "Where did I put that watershed tool?"
- Install Add-in
- Point it at your existing toolbox repos
- Instant searchable catalog of all tools
- VCS sync keeps everything organized

**No migration required.** Same YAML, same Python, same tools. Add-in just adds organization layer.

## Open Questions

### Q1: Add-in Required vs Optional?
**Should the Add-in be required to use the framework?**

Options:
- A: Add-in required (framework lives in Add-in)
- B: Framework bundled in each repo (standalone)
- C: Hybrid approach

**✅ DECISION: HYBRID (Option C) - Both Paths Supported**

**Path 1: Standalone (Framework Bundled)**
- Framework code lives in each toolbox repository
- Zero external dependencies
- Clone repo → add to Pro → works immediately
- Perfect for sharing individual toolboxes
- Users control framework version via Git
- **Use case:** "I want a portable toolbox I can share via zip file"

**Path 2: Add-in (Framework + VCS + Organization)**
- Framework lives in Add-in (optional optimization)
- Add-in provides:
  - **VCS integration** (GitHub, GitLab, Azure DevOps sync)
  - **Central tool registry** (all your tools, searchable)
  - **Cross-machine sync** (automatic)
  - **Tool discovery** ("find that tool I wrote last year")
- Multiple toolbox repositories managed in one UI
- **Use case:** "I have 50 tools across 10 projects and can't find anything"

**Why Both?**
- Standalone: Maximum portability, low barrier to entry, easy sharing
- Add-in: Solves tool organization and the "where did I put that tool?" problem
- Natural upgrade path: Start standalone, add Add-in when tool count grows
- Add-in's value is **organization/VCS**, not just framework delivery

**Framework Evolution (Non-Breaking):**
- Framework updates add features (new parameter types, better validation)
- Existing tools continue working (stable API contract)
- YAML schema can expand (new optional fields)
- Old YAML files still valid (backward compatible)
- Tool execute functions unchanged (same signature)
- **Result:** Your 5-year-old tools work with latest framework

### Q2: Toolbox Refresh Mechanism?
**How does Pro detect tool changes?**

Options:
- A: Manual refresh (Ctrl+R in Catalog) - user controlled
- B: Add-in triggers refresh via API - automatic
- C: File watcher in Add-in detects changes

**✅ DECISION: Hybrid**
- **Standalone mode:** Manual refresh (Ctrl+R) - standard Pro behavior
- **Add-in mode:** File watcher + auto-refresh (optional) - convenience feature
- Add-in can add "Refresh All Toolboxes" button

### Q3: Repository Management?
**How many toolbox repositories per project?**

Options:
- A: One repo per Pro project
- B: Multiple repos, switch in Add-in
- C: Multiple repos, all loaded simultaneously

**✅ DECISION: Multiple repos, all loaded simultaneously (Option C)**
- **Standalone mode:** N/A - user manages manually via Catalog
- **Add-in mode:** Manages multiple toolbox repositories
  - Personal tools repo
  - Team tools repo
  - Project-specific tools repo
- Add-in provides unified search/browse across all
- Each repo can be synced independently
- **This is the killer feature:** Central view of ALL your tools

### Q4: Tool Creation UI?
**How much UI for tool creation?**

Options:
- A: Full form-based tool builder (easy but complex to build)
- B: Templates only (manual YAML editing)
- C: Hybrid (wizard for simple tools, manual for complex)

**✅ DECISION: Start with templates (Option B), add wizard later**
- **Phase 1 (Standalone):** Template files + documentation
- **Phase 2 (Basic Add-in):** "New Tool" button creates from template
- **Phase 3 (Polish):** Optional wizard for common patterns
- Power users will always prefer YAML editing directly

## Development Phases

### Phase 0: Current State ✅
- Framework works as standalone Python toolbox
- Requires manual .pyt class wrappers
- Tools defined in YAML
- Proven concept, documented

### Phase 1: Stabilize Standalone Framework (1-3 months)
- Refactor to folder-per-tool structure
- Implement legacy tool support (both .pyt and .py)
- Document current standalone approach
- Create toolbox template repository
- Write "Getting Started" guide
- Test portability (zip distribution, network shares)
- Build 5-10 real tools to validate patterns (mix of new YAML + legacy)
- **Goal:** Prove standalone framework works great without Add-in
- **Goal:** Lower barrier to adoption with legacy tool support
- **Goal:** Build confidence in architecture before Add-in work

### Phase 2: Basic Add-in - Tool Catalog Manager (3-6 months)
- ArcGIS Pro Add-in UI panel
- **Tool Catalog:**
  - Central registry of all available tools
  - Add sources (VCS, local, network)
  - Automatic tool discovery and scanning
  - **Tagging system:**
    - Manual tags (user-defined)
    - Auto-tags (type, source, category)
    - Tag registry with autocomplete
    - Tag suggestions based on similarity
    - Tag usage statistics
  - **Tag-based search:**
    - Search by single or multiple tags (#buffer #spatial)
    - Combine tags with text search
    - Tag cloud visualization
    - Tag filtering (include/exclude)
    - Related tag suggestions
  - Search and filter across all sources
- **Source management:**
  - GitHub/GitLab/Azure DevOps integration
  - Auto-sync (pull latest changes)
  - Commit & push from UI
  - Conflict detection and resolution
- **Toolbox assignment:**
  - Browse catalog, assign tools to toolboxes
  - Same tool in multiple toolboxes (many-to-many)
  - YAML-driven, UI-managed (Add-in writes YAML)
  - Category overrides, tool aliases
- **Configuration management:**
  - catalog.yml (tool registry)
  - toolbox.yml (tool assignments)
  - User never manually edits YAML
- File watcher → auto-refresh on changes
- Dependency validation (warnings, not blocking)
- Built-in metadata loader (replaces standalone tool)
- Hide system tools when Add-in provides functionality
- **Goal:** Solve the "where's that tool?" problem with central catalog
- **Goal:** Make VCS transparent (no manual git commands)
- **Goal:** Enable tool reuse across projects (assign from catalog)

### Phase 3: Polish & Features (6-12 months)
- Tool creation wizard (form-based UI) - optional convenience
- Tool usage analytics ("I use this tool weekly, haven't used that in 2 years") - opt-in
- **Advanced tagging:**
  - Tag hierarchies ("hydrology.watershed.delineation")
  - Tag synonyms ("buffer" = "proximity")
  - Bulk tagging (select 10 tools → add tag to all)
  - Tag-based recommendations ("Tools tagged like this...")
  - Export/import tag schemas
  - Tag-based tool collections/bundles
- Better dependency management ("install missing packages" button) - convenience
- Tool templates library - quick-start helpers
- Bulk operations ("sync all repos", "refresh all toolboxes") - time savers
- **Goal:** Production-ready for daily use
- **Goal:** All features enhance workflow without requiring changes to existing tools

### Phase 4: Community (if adoption warrants)
- Sharing mechanisms
- Tool discovery across repos
- Ratings/reviews
- Trust indicators
- **Goal:** Enable organic ecosystem

## Common Concerns Addressed

### "Will framework updates break my tools?"
**No.** Framework only loads YAML and calls your execute function. Your business logic is independent. Framework updates add features (new parameter types, better validation) but maintain backward compatibility.

### "What if I need to work offline/in the field?"
**Not a concern.** Tools run from local directory. VCS sync requires connectivity, but tool execution doesn't. GIS geoprocessing is rarely done in the field anyway. Sync before you go → all tools available offline.

### "What if the Add-in stops being maintained?"
**Your tools still work.** Switch to standalone mode - same YAML, same Python, just bundle framework code in your repo. Or fork the framework. No vendor lock-in.

### "Do I need to learn Git?"
**No.** Standalone mode uses local folders (no Git). Add-in mode can auto-handle commits (Git becomes invisible). Only power users need to understand Git internals.

### "What about framework version conflicts?"
**Two approaches, your choice:**
- **Standalone:** Each toolbox bundles its framework version (isolated, user controlled)
- **Add-in:** All toolboxes use Add-in framework version (centrally managed, tested updates)

Migration path exists if you need to switch between modes.

## Success Metrics

**Standalone success (Phase 1):**
- "I use this daily for my own tools"
- "It's easier than traditional .pyt files"
- "I can share toolboxes as simple zip files"
- "Clone and go - no setup required"
- "I migrated 3 legacy tools in 10 minutes (just copied .pyt files)"

**Add-in success (Phase 2):**
- "I found a tool from 18 months ago in 5 seconds by searching the catalog"
- "I typed '#buffer #hydrology' and found exactly the 2 tools I needed"
- "The Add-in suggested tags for my new tool - saved me time organizing"
- "I have 50 tools from 5 sources, all tagged and searchable in one place"
- "I reused the same buffer tool in 3 different project toolboxes"
- "My work/home/field laptop all stay in sync automatically"
- "I added a GitHub repo and 20 tools appeared instantly with auto-tags"
- "I've never manually edited catalog.yml or toolbox.yml"
- "I never run git commands anymore - Add-in handles it"

**Team success (Phase 2-3):**
- "My colleagues asked for access"
- "We share tools naturally now"
- "Onboarding new team members is easier"

**Community success (Phase 4):**
- "People I don't know are using it"
- "Getting unsolicited feature requests"
- "Esri people are aware of it"

## What If Esri Adopts It?

**Best outcome:** Esri adds native YAML toolbox support to ArcGIS Pro

**Response:** Celebrate! Problem solved at scale, everyone benefits.

**Philosophy:** Build something useful, share it freely, let adoption happen organically. Credit doesn't matter if the problem gets solved.

## Next Steps

1. **Use current framework** - Build real tools, find rough edges
2. **Document workflows** - Write guide for manual Git + framework usage
3. **Test portability** - Clone repo to different machine, verify it works
4. **Identify pain points** - What's annoying? That's the Add-in feature list
5. **Build incrementally** - Don't build Add-in until framework is proven daily

**Remember:** Solve your own problem first. Everything else is future speculation until you've proven the core workflow works for real daily use.

---

## References

- [Configuration Guide](configuration-guide.md) - Current framework documentation
- [Architecture](development/architecture.md) - Technical design details
- [Testing Guide](development/testing.md) - How to test tools

## Notes

This is a living document capturing conceptual thinking. As implementation progresses, migrate concrete decisions to proper documentation and archive speculative sections.
