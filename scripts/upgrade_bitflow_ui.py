from pathlib import Path

P = Path('app/src/main/java/com/example/torrentor/MainActivity.kt')
s = P.read_text(encoding='utf-8')

if 'import android.view.View' not in s:
    s = s.replace('import android.widget.*\n', 'import android.widget.*\nimport android.view.View\n', 1)


def replace_function(source: str, signature: str, replacement: str) -> str:
    start = source.find(signature)
    if start < 0:
        raise SystemExit(f'Could not find function: {signature}')
    brace = source.find('{', start)
    if brace < 0:
        raise SystemExit(f'Could not find function body: {signature}')
    depth = 0
    in_string = False
    escaped = False
    in_line_comment = False
    in_block_comment = False
    i = brace
    while i < len(source):
        c = source[i]
        n = source[i + 1] if i + 1 < len(source) else ''
        if in_line_comment:
            if c == '\n':
                in_line_comment = False
        elif in_block_comment:
            if c == '*' and n == '/':
                in_block_comment = False
                i += 1
        elif in_string:
            if escaped:
                escaped = False
            elif c == '\\':
                escaped = True
            elif c == '"':
                in_string = False
        else:
            if c == '/' and n == '/':
                in_line_comment = True
                i += 1
            elif c == '/' and n == '*':
                in_block_comment = True
                i += 1
            elif c == '"':
                in_string = True
            elif c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    return source[:start] + replacement.rstrip() + source[i + 1:]
        i += 1
    raise SystemExit(f'Unbalanced function body: {signature}')


MAIN = r'''    private fun showMainScreen() {
        stopNetworkFeaturesAutoRefresh()
        stopStorageAutoRefresh()
        stopGlobalStatsAutoRefresh()
        stopRssUiRefresh()
        stopLogUiRefresh()
        currentDetailsTab = ""
        currentDetailsTorrentIndex = -1
        currentDetailsContentText = null
        currentDetailsFileListLayout = null

        val d = resources.displayMetrics.density
        fun dp(v: Int) = (v * d).toInt()
        val bg = Color.parseColor("#F5F7FB")
        val fg = Color.parseColor("#111827")
        val muted = Color.parseColor("#6B7280")
        val primary = Color.parseColor("#2563EB")
        val border = Color.parseColor("#E5E7EB")

        fun button(label: String, action: () -> Unit) = TextView(this).apply {
            text = label
            textSize = 13f
            gravity = android.view.Gravity.CENTER
            setPadding(dp(12), 0, dp(12), 0)
            setTextColor(fg)
            background = android.graphics.drawable.GradientDrawable().apply {
                cornerRadius = dp(10).toFloat()
                setColor(Color.WHITE)
                setStroke(dp(1), border)
            }
            setOnClickListener { action() }
        }

        val content = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(16), dp(16), dp(16), dp(92))
            setBackgroundColor(bg)
        }
        val scroll = ScrollView(this).apply {
            isFillViewport = true
            addView(content)
        }

        val header = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = android.view.Gravity.CENTER_VERTICAL
        }
        val logo = ImageView(this).apply {
            setImageResource(R.drawable.bitflow_logo)
            scaleType = ImageView.ScaleType.CENTER_INSIDE
        }
        header.addView(logo, LinearLayout.LayoutParams(dp(42), dp(42)).apply { rightMargin = dp(10) })
        val brand = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        brand.addView(TextView(this).apply {
            text = "BitFlow"
            textSize = 25f
            setTypeface(typeface, android.graphics.Typeface.BOLD)
            setTextColor(fg)
        })
        brand.addView(TextView(this).apply {
            text = "Torrent Downloader"
            textSize = 12f
            setTextColor(muted)
        })
        header.addView(brand, LinearLayout.LayoutParams(0, -2, 1f))
        header.addView(TextView(this).apply {
            text = "Downloads"
            textSize = 13f
            setTextColor(muted)
            gravity = android.view.Gravity.CENTER
        }, LinearLayout.LayoutParams(-2, dp(42)))
        content.addView(header)
        content.addView(Space(this).apply { layoutParams = LinearLayout.LayoutParams(1, dp(12)) })

        val search = EditText(this).apply {
            hint = "Search downloads"
            setSingleLine(true)
            textSize = 14f
            setText(searchQuery)
            setSelection(text.length)
            setPadding(dp(14), 0, dp(14), 0)
            setTextColor(fg)
            setHintTextColor(muted)
            background = android.graphics.drawable.GradientDrawable().apply {
                cornerRadius = dp(12).toFloat()
                setColor(Color.WHITE)
                setStroke(dp(1), border)
            }
            addTextChangedListener(object : TextWatcher {
                override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
                override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {
                    searchQuery = s?.toString() ?: ""
                    updateTorrentList()
                }
                override fun afterTextChanged(s: Editable?) {}
            })
        }
        content.addView(search, LinearLayout.LayoutParams(-1, dp(48)))
        content.addView(Space(this).apply { layoutParams = LinearLayout.LayoutParams(1, dp(10)) })

        val filterScroll = HorizontalScrollView(this).apply { isHorizontalScrollBarEnabled = false }
        val filters = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        arrayOf("All", "Active", "Paused", "Completed").forEach { label ->
            val chip = TextView(this).apply {
                text = label
                textSize = 13f
                gravity = android.view.Gravity.CENTER
                setPadding(dp(12), 0, dp(12), 0)
                setTextColor(if (activeFilter == label) Color.WHITE else fg)
                background = android.graphics.drawable.GradientDrawable().apply {
                    cornerRadius = dp(20).toFloat()
                    setColor(if (activeFilter == label) primary else Color.WHITE)
                    if (activeFilter != label) setStroke(dp(1), border)
                }
                setOnClickListener {
                    activeFilter = label
                    torrentListViewPrefs().edit().putString("filter", label).apply()
                    selectedTorrents.clear()
                    selectMode = false
                    showMainScreen()
                }
            }
            filters.addView(chip, LinearLayout.LayoutParams(dp(88), dp(40)).apply { rightMargin = dp(8) })
        }
        filterScroll.addView(filters)
        content.addView(filterScroll)
        content.addView(Space(this).apply { layoutParams = LinearLayout.LayoutParams(1, dp(8)) })

        val toolbar = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = android.view.Gravity.CENTER_VERTICAL
        }
        toolbar.addView(TextView(this).apply {
            text = "Downloads"
            textSize = 20f
            setTypeface(typeface, android.graphics.Typeface.BOLD)
            setTextColor(fg)
        }, LinearLayout.LayoutParams(0, -2, 1f))
        toolbar.addView(button("Sort") {
            AlertDialog.Builder(this@MainActivity)
                .setTitle("Sort downloads")
                .setItems(TORRENT_SORT_MODES) { _, which ->
                    sortMode = TORRENT_SORT_MODES[which]
                    torrentListViewPrefs().edit().putString("sort", sortMode).apply()
                    showMainScreen()
                }.show()
        }, LinearLayout.LayoutParams(-2, dp(42)))
        content.addView(toolbar)

        val selection = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding(0, dp(8), 0, dp(8))
        }
        selection.addView(button(if (selectMode) "Done" else "Select") {
            selectMode = !selectMode
            selectedTorrents.clear()
            showMainScreen()
        }, LinearLayout.LayoutParams(0, dp(40), 1f).apply { rightMargin = dp(8) })
        selection.addView(button("Select all") {
            if (selectMode) {
                selectedTorrents.clear()
                selectedTorrents.addAll(getVisibleTorrentIndexes())
                updateTorrentList()
            }
        }, LinearLayout.LayoutParams(0, dp(40), 1f))
        content.addView(selection)

        if (selectMode) {
            val bulk = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
            bulk.addView(button("Pause") {
                selectedTorrents.toList().forEach { sendTorrentAction("PAUSE_TORRENT", it) }
                selectedTorrents.clear(); selectMode = false; showMainScreen()
            }, LinearLayout.LayoutParams(0, dp(40), 1f).apply { rightMargin = dp(6) })
            bulk.addView(button("Resume") {
                selectedTorrents.toList().forEach { sendTorrentAction("RESUME_TORRENT", it) }
                selectedTorrents.clear(); selectMode = false; showMainScreen()
            }, LinearLayout.LayoutParams(0, dp(40), 1f).apply { rightMargin = dp(6) })
            bulk.addView(button("Recheck") {
                selectedTorrents.toList().forEach { sendTorrentAction("RECHECK_TORRENT", it) }
                selectedTorrents.clear(); selectMode = false; showMainScreen()
            }, LinearLayout.LayoutParams(0, dp(40), 1f))
            content.addView(bulk)
        }

        val speedCard = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(14), dp(10), dp(14), dp(10))
            background = android.graphics.drawable.GradientDrawable().apply {
                cornerRadius = dp(14).toFloat(); setColor(Color.WHITE); setStroke(dp(1), border)
            }
        }
        speedGraphText = TextView(this).apply { text = "↓ 0 KB/s     ↑ 0 KB/s"; textSize = 13f; setTextColor(muted) }
        speedGraphView = SpeedGraphView(this)
        speedGraphView.setBackgroundColor(Color.WHITE)
        speedCard.addView(speedGraphText, LinearLayout.LayoutParams(-1, dp(25)))
        speedCard.addView(speedGraphView, LinearLayout.LayoutParams(-1, dp(70)))
        content.addView(speedCard, LinearLayout.LayoutParams(-1, dp(112)).apply { topMargin = dp(8); bottomMargin = dp(12) })

        listLayout = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        content.addView(listLayout, LinearLayout.LayoutParams(-1, -2))
        content.addView(TextView(this).apply {
            text = "Tap a download for its full dashboard: files, peers, trackers, web seeds, swarm, pieces, statistics and controls."
            textSize = 12f; setTextColor(muted); setPadding(0, dp(8), 0, dp(4))
        })

        setContentView(wrapWithBitFlowBottomNav(scroll, "home"))
        isOnMainScreen = true
        updateTorrentList()
    }
'''

SETTINGS = r'''    private fun showSettingsScreen() {
        stopNetworkFeaturesAutoRefresh()
        stopStorageAutoRefresh()
        stopGlobalStatsAutoRefresh()
        stopRssUiRefresh()
        stopLogUiRefresh()
        currentDetailsTab = ""
        currentDetailsTorrentIndex = -1
        currentDetailsContentText = null
        currentDetailsFileListLayout = null

        val d = resources.displayMetrics.density
        fun dp(v: Int) = (v * d).toInt()
        val bg = Color.parseColor("#F5F7FB")
        val fg = Color.parseColor("#111827")
        val muted = Color.parseColor("#6B7280")
        val border = Color.parseColor("#E5E7EB")

        val content = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(16), dp(18), dp(16), dp(92))
            setBackgroundColor(bg)
        }
        val scroll = ScrollView(this).apply { isFillViewport = true; addView(content) }
        content.addView(TextView(this).apply {
            text = "Settings"; textSize = 28f; setTypeface(typeface, android.graphics.Typeface.BOLD); setTextColor(fg)
        })
        content.addView(TextView(this).apply {
            text = "All BitFlow features in one place"; textSize = 13f; setTextColor(muted); setPadding(0, dp(4), 0, dp(16))
        })

        fun row(title: String, desc: String, action: () -> Unit) = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = android.view.Gravity.CENTER_VERTICAL
            setPadding(dp(14), dp(11), dp(10), dp(11))
            background = android.graphics.drawable.GradientDrawable().apply {
                cornerRadius = dp(12).toFloat(); setColor(Color.WHITE); setStroke(dp(1), border)
            }
            setOnClickListener { action() }
            addView(TextView(this@MainActivity).apply { text = "•"; textSize = 22f; setTextColor(Color.parseColor("#2563EB")); gravity = android.view.Gravity.CENTER }, LinearLayout.LayoutParams(dp(30), dp(42)))
            val box = LinearLayout(this@MainActivity).apply { orientation = LinearLayout.VERTICAL }
            box.addView(TextView(this@MainActivity).apply { text = title; textSize = 15f; setTypeface(typeface, android.graphics.Typeface.BOLD); setTextColor(fg) })
            box.addView(TextView(this@MainActivity).apply { text = desc; textSize = 12f; setTextColor(muted); setPadding(0, dp(3), 0, 0) })
            addView(box, LinearLayout.LayoutParams(0, -2, 1f))
            addView(TextView(this@MainActivity).apply { text = "›"; textSize = 24f; setTextColor(muted); gravity = android.view.Gravity.CENTER }, LinearLayout.LayoutParams(dp(24), -1))
        }
        fun section(title: String, subtitle: String, items: List<Triple<String, String, () -> Unit>>) {
            content.addView(TextView(this).apply { text = title; textSize = 13f; setTypeface(typeface, android.graphics.Typeface.BOLD); setTextColor(muted); setPadding(dp(2), dp(8), dp(2), dp(4)) })
            content.addView(TextView(this).apply { text = subtitle; textSize = 11f; setTextColor(muted); setPadding(dp(2), 0, dp(2), dp(6)) })
            items.forEachIndexed { i, item ->
                content.addView(row(item.first, item.second, item.third), LinearLayout.LayoutParams(-1, -2).apply { bottomMargin = if (i == items.lastIndex) dp(5) else dp(7) })
            }
        }

        section("Downloads", "Storage and transfer", listOf(
            Triple("Save folder", "Choose the download folder and create folders", { showSaveFolderScreen() }),
            Triple("Speed limits", "Global download and upload limits", { showSpeedLimitsScreen() }),
            Triple("Storage", "Free space and low-storage threshold", { showStorageScreen() })
        ))
        section("Network", "Connectivity and peers", listOf(
            Triple("Connection", "Listening and connectivity diagnostics", { showConnectionScreen() }),
            Triple("Network features", "DHT, PEX, LSD and protocol encryption", { showNetworkFeaturesScreen() })
        ))
        section("Discovery", "Find new torrents", listOf(
            Triple("Online search", "Providers, search filters and sorting", { showOnlineSearchScreen() }),
            Triple("RSS feeds", "Feeds, refresh and auto-download", { showRssScreen() })
        ))
        section("Diagnostics", "Inspect the engine", listOf(
            Triple("Statistics", "Live session and torrent statistics", { showGlobalStatsScreen() }),
            Triple("Execution log", "INFO/WARNING/ERROR logs and actions", { showExecutionLogScreen() })
        ))
        section("Appearance", "Personalize BitFlow", listOf(
            Triple("Theme", "Current theme: ${currentThemeName()}", { switchTheme() })
        ))
        section("About", "Application information", listOf(
            Triple("About BitFlow", "Version 1.0.0 and app information", { showAboutDialog() })
        ))

        setContentView(wrapWithBitFlowBottomNav(scroll, "settings"))
    }

    private fun wrapWithBitFlowBottomNav(content: View, selected: String): View {
        val d = resources.displayMetrics.density
        fun dp(v: Int) = (v * d).toInt()
        val fg = Color.parseColor("#111827")
        val muted = Color.parseColor("#9CA3AF")
        val primary = Color.parseColor("#2563EB")
        val root = FrameLayout(this)
        root.addView(content, FrameLayout.LayoutParams(-1, -1))
        val bar = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = android.view.Gravity.CENTER
            setPadding(dp(10), dp(4), dp(10), dp(6))
            setBackgroundColor(Color.WHITE)
            elevation = dp(8).toFloat()
        }
        fun item(icon: String, label: String, key: String, action: () -> Unit) = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = android.view.Gravity.CENTER
            setOnClickListener { action() }
            addView(TextView(this@MainActivity).apply {
                text = icon; textSize = 23f; gravity = android.view.Gravity.CENTER
                setTextColor(if (selected == key) primary else muted)
                setTypeface(typeface, if (selected == key) android.graphics.Typeface.BOLD else android.graphics.Typeface.NORMAL)
            }, LinearLayout.LayoutParams(-1, dp(31)))
            addView(TextView(this@MainActivity).apply {
                text = label; textSize = 10f; gravity = android.view.Gravity.CENTER
                setTextColor(if (selected == key) fg else muted)
                setTypeface(typeface, if (selected == key) android.graphics.Typeface.BOLD else android.graphics.Typeface.NORMAL)
            }, LinearLayout.LayoutParams(-1, dp(18)))
        }
        bar.addView(item("⌂", "Home", "home") { showMainScreen() }, LinearLayout.LayoutParams(0, dp(52), 1f))
        bar.addView(item("＋", "Add", "add") { showAddDownloadDialog() }, LinearLayout.LayoutParams(0, dp(52), 1f))
        bar.addView(item("⚙", "Settings", "settings") { showSettingsScreen() }, LinearLayout.LayoutParams(0, dp(52), 1f))
        root.addView(bar, FrameLayout.LayoutParams(-1, dp(64)).apply { gravity = android.view.Gravity.BOTTOM })
        return root
    }
'''

s = replace_function(s, 'private fun showMainScreen()', MAIN)
s = replace_function(s, 'private fun showSettingsScreen()', SETTINGS)

# The modern Home filter calls this helper; add it once if the project does not already have it.
if 'private fun getVisibleTorrentIndexes()' not in s:
    marker = '    private fun updateTorrentList()'
    helper = '''    private fun getVisibleTorrentIndexes(): List<Int> {\n        val out = mutableListOf<Int>()\n        val data = getTorrentList()\n        for (i in data.indices) {\n            val line = data[i]\n            if (searchQuery.isNotBlank() && !line.contains(searchQuery, ignoreCase = true)) continue\n            val matches = when (activeFilter) {\n                "Active" -> line.contains("Downloading", true) || line.contains("Seeding", true)\n                "Paused" -> line.contains("Paused", true)\n                "Completed" -> line.contains("Completed", true)\n                else -> true\n            }\n            if (matches) out.add(i)\n        }\n        return out\n    }\n\n'''
    if marker in s:
        s = s.replace(marker, helper + marker, 1)

P.write_text(s, encoding='utf-8')
print('Safe BitFlow UI upgrade applied')
