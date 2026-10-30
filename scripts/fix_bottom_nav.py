from pathlib import Path

path = Path("app/src/main/java/com/example/torrentor/MainActivity.kt")
text = path.read_text()

if "// BITFLOW_BOTTOM_NAV_V1" in text:
    print("Bottom navigation already present; nothing to change.")
    raise SystemExit(0)

text = text.replace(
    "setPadding(dp(16), dp(16), dp(16), dp(20))",
    "setPadding(dp(16), dp(16), dp(16), dp(92))",
    1,
)

old_add = '''        root.addView(Space(this).apply { layoutParams = LinearLayout.LayoutParams(1, dp(12)) })
        root.addView(button("+  Add download", true) { showAddDownloadDialog() }, LinearLayout.LayoutParams(-1, dp(48)))
'''
if old_add not in text:
    raise SystemExit("Expected Add download block was not found; refusing unsafe edit")
text = text.replace(old_add, "", 1)

old_set = '''        setContentView(scroll)
        isOnMainScreen = true
'''
new_set = '''        // BITFLOW_BOTTOM_NAV_V1: fixed navigation stays outside the scrolling content.
        val bottomBar = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = android.view.Gravity.CENTER
            setPadding(dp(8), dp(6), dp(8), dp(6))
            setBackgroundColor(Color.WHITE)
            elevation = dp(5).toFloat()
        }

        fun navItem(label: String, selected: Boolean = false, action: () -> Unit): TextView {
            return TextView(this).apply {
                text = label
                textSize = 13f
                gravity = android.view.Gravity.CENTER
                setTypeface(typeface, android.graphics.Typeface.BOLD)
                setTextColor(if (selected) Color.WHITE else fg)
                background = android.graphics.drawable.GradientDrawable().apply {
                    cornerRadius = dp(10).toFloat()
                    setColor(if (selected) primary else Color.WHITE)
                    if (!selected) setStroke(dp(1), border)
                }
                setOnClickListener { action() }
            }
        }

        bottomBar.addView(
            navItem("Downloads", true) { showMainScreen() },
            LinearLayout.LayoutParams(0, dp(52), 1f).apply { rightMargin = dp(6) }
        )
        bottomBar.addView(
            navItem("+ Add") { showAddDownloadDialog() },
            LinearLayout.LayoutParams(0, dp(52), 1f).apply { rightMargin = dp(6) }
        )
        bottomBar.addView(
            navItem("Settings") { showSettingsScreen() },
            LinearLayout.LayoutParams(0, dp(52), 1f)
        )

        val screen = FrameLayout(this)
        screen.addView(scroll, FrameLayout.LayoutParams(-1, -1))
        screen.addView(
            bottomBar,
            FrameLayout.LayoutParams(-1, dp(64)).apply {
                gravity = android.view.Gravity.BOTTOM
            }
        )
        setContentView(screen)
        isOnMainScreen = true
'''
if old_set not in text:
    raise SystemExit("Expected setContentView block was not found; refusing unsafe edit")
text = text.replace(old_set, new_set, 1)

path.write_text(text)
print("Bottom navigation restored.")
