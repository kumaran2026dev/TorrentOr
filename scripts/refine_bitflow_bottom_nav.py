from pathlib import Path

path = Path("app/src/main/java/com/example/torrentor/MainActivity.kt")
text = path.read_text(encoding="utf-8")

helper_marker = "    private fun wrapWithBitFlowBottomNav(content: android.view.View, selected: String): FrameLayout {"
if helper_marker not in text:
    marker = "    private fun showAddDownloadDialog() {"
    helper = '''    private fun wrapWithBitFlowBottomNav(content: android.view.View, selected: String): FrameLayout {
        val d = resources.displayMetrics.density
        fun dp(v: Int) = (v * d).toInt()
        val fg = Color.parseColor("#111827")
        val muted = Color.parseColor("#9CA3AF")
        val border = Color.parseColor("#E5E7EB")

        val root = FrameLayout(this)
        root.addView(content, FrameLayout.LayoutParams(-1, -1))

        val bar = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = android.view.Gravity.CENTER
            setPadding(dp(12), dp(4), dp(12), dp(5))
            setBackgroundColor(Color.WHITE)
            elevation = dp(8).toFloat()
        }

        fun item(icon: String, label: String, key: String, action: () -> Unit): View {
            return LinearLayout(this).apply {
                orientation = LinearLayout.VERTICAL
                gravity = android.view.Gravity.CENTER
                setPadding(0, dp(2), 0, dp(2))
                val iconView = TextView(this@MainActivity).apply {
                    text = icon
                    textSize = if (key == "add") 28f else 24f
                    gravity = android.view.Gravity.CENTER
                    setTextColor(if (selected == key) fg else muted)
                    setTypeface(typeface, android.graphics.Typeface.BOLD)
                }
                addView(iconView, LinearLayout.LayoutParams(-1, dp(30)))
                if (key != "add") {
                    addView(TextView(this@MainActivity).apply {
                        text = label
                        textSize = 10f
                        gravity = android.view.Gravity.CENTER
                        setTextColor(if (selected == key) fg else muted)
                        setTypeface(typeface, android.graphics.Typeface.BOLD)
                    }, LinearLayout.LayoutParams(-1, dp(16)))
                }
                setOnClickListener { action() }
            }
        }

        bar.addView(item("⌂", "Home", "home") { showMainScreen() }, LinearLayout.LayoutParams(0, dp(50), 1f))
        bar.addView(item("＋", "", "add") { showAddDownloadDialog() }, LinearLayout.LayoutParams(0, dp(50), 1f))
        bar.addView(item("⚙", "Settings", "settings") { showSettingsScreen() }, LinearLayout.LayoutParams(0, dp(50), 1f))

        root.addView(bar, FrameLayout.LayoutParams(-1, dp(62)).apply { gravity = android.view.Gravity.BOTTOM })
        return root
    }

'''
    if marker not in text:
        raise SystemExit("showAddDownloadDialog marker not found")
    text = text.replace(marker, helper + marker, 1)

start = text.find("        // BITFLOW_BOTTOM_NAV_V1: fixed navigation stays outside the scrolling content.")
if start == -1:
    raise SystemExit("old bottom navigation marker not found")
end_marker = "        setContentView(screen)"
end = text.find(end_marker, start)
if end == -1:
    raise SystemExit("old bottom navigation end not found")
end += len(end_marker)
text = text[:start] + '        setContentView(wrapWithBitFlowBottomNav(scroll, "home"))' + text[end:]

old_settings = '        setContentView(ScrollView(this).apply { isFillViewport = true; addView(root) })'
new_settings = '        setContentView(wrapWithBitFlowBottomNav(ScrollView(this).apply { isFillViewport = true; addView(root) }, "settings"))'
if old_settings not in text:
    raise SystemExit("settings content line not found")
text = text.replace(old_settings, new_settings, 1)

path.write_text(text, encoding="utf-8")
print("BitFlow bottom navigation refined successfully")
