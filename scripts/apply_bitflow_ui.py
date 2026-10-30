from pathlib import Path

path = Path('app/src/main/java/com/example/torrentor/MainActivity.kt')
text = path.read_text(encoding='utf-8')
start = text.index('    private fun showMainScreen()')
brace_start = text.index('{', start)
depth = 0
end = None
in_string = False
escaped = False
line_comment = False
block_comment = False
i = brace_start
while i < len(text):
    c = text[i]
    n = text[i + 1] if i + 1 < len(text) else ''
    if line_comment:
        if c == '\n': line_comment = False
    elif block_comment:
        if c == '*' and n == '/': block_comment = False; i += 1
    elif in_string:
        if escaped: escaped = False
        elif c == '\\': escaped = True
        elif c == '"': in_string = False
    else:
        if c == '/' and n == '/': line_comment = True; i += 1
        elif c == '/' and n == '*': block_comment = True; i += 1
        elif c == '"': in_string = True
        elif c == '{': depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    i += 1
if end is None:
    raise SystemExit('Could not locate showMainScreen() end')

new_code = '''    private fun showMainScreen() {
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
        val bg = Color.parseColor("#F6F7F9")
        val fg = Color.parseColor("#202124")
        val muted = Color.parseColor("#6B7280")
        val primary = Color.parseColor("#2563EB")
        val border = Color.parseColor("#D9DEE7")

        fun button(label: String, primaryButton: Boolean = false, action: () -> Unit) = Button(this).apply {
            text = label
            isAllCaps = false
            textSize = 14f
            minHeight = dp(44)
            setTextColor(if (primaryButton) Color.WHITE else fg)
            background = android.graphics.drawable.GradientDrawable().apply {
                cornerRadius = dp(10).toFloat()
                if (primaryButton) setColor(primary) else { setColor(Color.WHITE); setStroke(dp(1), border) }
            }
            setOnClickListener { action() }
        }
        fun heading(label: String, size: Float = 20f) = TextView(this).apply {
            text = label
            textSize = size
            setTextColor(fg)
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        }

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(16), dp(16), dp(16), dp(20))
            setBackgroundColor(bg)
        }
        val scroll = ScrollView(this).apply { isFillViewport = true }
        scroll.addView(root)

        val header = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; gravity = android.view.Gravity.CENTER_VERTICAL }
        val logo = ImageView(this).apply { setImageResource(R.drawable.bitflow_logo); scaleType = ImageView.ScaleType.CENTER_INSIDE }
        header.addView(logo, LinearLayout.LayoutParams(dp(44), dp(44)).apply { rightMargin = dp(10) })
        val brand = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        brand.addView(heading("BitFlow", 24f))
        brand.addView(TextView(this).apply { text = "Torrent Downloader"; textSize = 12f; setTextColor(muted) })
        header.addView(brand, LinearLayout.LayoutParams(0, -2, 1f))
        header.addView(button("Settings") { showSettingsScreen() }, LinearLayout.LayoutParams(-2, dp(44)))
        root.addView(header)
        root.addView(Space(this).apply { layoutParams = LinearLayout.LayoutParams(1, dp(12)) })

        val search = EditText(this).apply {
            hint = "Search downloads"
            setSingleLine(true)
            textSize = 14f
            setText(searchQuery)
            setSelection(text.length)
            setPadding(dp(14), 0, dp(14), 0)
            setTextColor(fg)
            setHintTextColor(muted)
            background = android.graphics.drawable.GradientDrawable().apply { cornerRadius = dp(10).toFloat(); setColor(Color.WHITE); setStroke(dp(1), border) }
            addTextChangedListener(object : TextWatcher {
                override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
                override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) { searchQuery = s?.toString() ?: ""; updateTorrentList() }
                override fun afterTextChanged(s: Editable?) {}
            })
        }
        root.addView(search, LinearLayout.LayoutParams(-1, dp(48)))
        root.addView(Space(this).apply { layoutParams = LinearLayout.LayoutParams(1, dp(10)) })

        val filters = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        for (label in arrayOf("All", "Active", "Paused", "Completed")) {
            filters.addView(button(label, activeFilter == label) {
                activeFilter = label
                torrentListViewPrefs().edit().putString("filter", label).apply()
                selectedTorrents.clear(); selectMode = false; showMainScreen()
            }, LinearLayout.LayoutParams(0, dp(42), 1f).apply { rightMargin = dp(5) })
        }
        root.addView(filters)

        val toolbar = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; gravity = android.view.Gravity.CENTER_VERTICAL }
        toolbar.addView(heading("Downloads", 19f), LinearLayout.LayoutParams(0, -2, 1f))
        toolbar.addView(button("Sort") {
            AlertDialog.Builder(this@MainActivity).setTitle("Sort downloads").setItems(TORRENT_SORT_MODES) { _, which ->
                sortMode = TORRENT_SORT_MODES[which]
                torrentListViewPrefs().edit().putString("sort", sortMode).apply()
                showMainScreen()
            }.show()
        }, LinearLayout.LayoutParams(-2, dp(44)))
        root.addView(toolbar)

        val selectRow = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        selectRow.addView(button(if (selectMode) "Done" else "Select", selectMode) { selectMode = !selectMode; selectedTorrents.clear(); showMainScreen() }, LinearLayout.LayoutParams(0, dp(42), 1f).apply { rightMargin = dp(6) })
        selectRow.addView(button("Select all") { if (selectMode) { selectedTorrents.clear(); selectedTorrents.addAll(getVisibleTorrentIndexes()); updateTorrentList() } }, LinearLayout.LayoutParams(0, dp(42), 1f))
        root.addView(selectRow)

        if (selectMode) {
            val bulk = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
            bulk.addView(button("Pause") { selectedTorrents.toList().forEach { sendTorrentAction("PAUSE_TORRENT", it) }; selectedTorrents.clear(); selectMode = false; showMainScreen() }, LinearLayout.LayoutParams(0, dp(42), 1f).apply { rightMargin = dp(5) })
            bulk.addView(button("Resume") { selectedTorrents.toList().forEach { sendTorrentAction("RESUME_TORRENT", it) }; selectedTorrents.clear(); selectMode = false; showMainScreen() }, LinearLayout.LayoutParams(0, dp(42), 1f).apply { rightMargin = dp(5) })
            bulk.addView(button("Recheck") { selectedTorrents.toList().forEach { sendTorrentAction("RECHECK_TORRENT", it) }; selectedTorrents.clear(); selectMode = false; showMainScreen() }, LinearLayout.LayoutParams(0, dp(42), 1f))
            root.addView(bulk)
        }

        listLayout = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        root.addView(listLayout, LinearLayout.LayoutParams(-1, -2))
        root.addView(Space(this).apply { layoutParams = LinearLayout.LayoutParams(1, dp(12)) })
        root.addView(button("+  Add download", true) { showAddDownloadDialog() }, LinearLayout.LayoutParams(-1, dp(48)))

        speedGraphText = TextView(this)
        speedGraphView = SpeedGraphView(this)
        speedGraphText.visibility = android.view.View.GONE
        speedGraphView.visibility = android.view.View.GONE
        setContentView(scroll)
        isOnMainScreen = true
        updateTorrentList()
    }

    private fun showAddDownloadDialog() {
        val input = EditText(this).apply { hint = "magnet:?xt=urn:btih:..."; minLines = 3; gravity = android.view.Gravity.TOP }
        val box = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setPadding(24, 8, 24, 0); addView(input, LinearLayout.LayoutParams(-1, 120)) }
        val dialog = AlertDialog.Builder(this).setTitle("Add download").setView(box).setNegativeButton("Cancel", null).setNeutralButton("Choose .torrent", null).setPositiveButton("Add magnet", null).create()
        dialog.setOnShowListener {
            dialog.getButton(AlertDialog.BUTTON_NEUTRAL).setOnClickListener { dialog.dismiss(); pickTorrent.launch("application/x-bittorrent") }
            dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener {
                val magnet = input.text.toString().trim()
                if (magnet.isBlank()) { input.error = "Enter a magnet link"; return@setOnClickListener }
                dialog.dismiss(); showMagnetMetadataScreen(magnet)
            }
        }
        dialog.show()
    }

    private fun showSettingsScreen() {
        val d = resources.displayMetrics.density
        fun dp(v: Int) = (v * d).toInt()
        val root = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setPadding(dp(18), dp(18), dp(18), dp(24)); setBackgroundColor(Color.parseColor("#F6F7F9")) }
        root.addView(TextView(this).apply { text = "Settings"; textSize = 24f; setTypeface(typeface, android.graphics.Typeface.BOLD); setTextColor(Color.parseColor("#202124")); setPadding(0, 0, 0, dp(14)) })
        fun item(label: String, action: () -> Unit) {
            root.addView(Button(this).apply { text = label; isAllCaps = false; textSize = 15f; gravity = android.view.Gravity.START or android.view.Gravity.CENTER_VERTICAL; setPadding(dp(16), 0, dp(16), 0); setOnClickListener { action() } }, LinearLayout.LayoutParams(-1, dp(52)).apply { bottomMargin = dp(8) })
        }
        item("Downloads · Save folder") { showSaveFolderScreen() }
        item("Downloads · Speed limits") { showSpeedLimitsScreen() }
        item("Network · Connection") { showConnectionScreen() }
        item("Network · Network features") { showNetworkFeaturesScreen() }
        item("Discovery · Online search") { showOnlineSearchScreen() }
        item("Discovery · RSS feeds") { showRssScreen() }
        item("Diagnostics · Statistics") { showGlobalStatsScreen() }
        item("Diagnostics · Execution log") { showExecutionLogScreen() }
        item("Diagnostics · Storage") { showStorageScreen() }
        item("Appearance · Theme: ${currentThemeName()}") { switchTheme() }
        item("About BitFlow") { showAboutDialog() }
        root.addView(Button(this).apply { text = "Back to downloads"; isAllCaps = false; setOnClickListener { showMainScreen() } }, LinearLayout.LayoutParams(-1, dp(48)))
        setContentView(ScrollView(this).apply { isFillViewport = true; addView(root) })
    }

    private fun showAboutDialog() {
        AlertDialog.Builder(this).setTitle("BitFlow").setMessage("BitFlow: Torrent Downloader\\nVersion 1.0.0\\n\\nFast, simple torrent downloading for Android.").setPositiveButton("OK", null).show()
    }
'''

path.write_text(text[:start] + new_code + text[end:], encoding='utf-8')
print('UI migration applied; original MainActivity methods after showMainScreen were preserved.')
