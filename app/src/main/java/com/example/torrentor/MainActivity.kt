package com.example.torrentor

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Intent
import android.content.SharedPreferences
import android.graphics.Color
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.StatFs
import android.provider.DocumentsContract
import android.text.Editable
import android.text.TextWatcher
import android.util.Log
import android.webkit.MimeTypeMap
import android.widget.*
import androidx.activity.OnBackPressedCallback
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.FileProvider
import androidx.core.net.toUri
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import org.xmlpull.v1.XmlPullParser
import org.xmlpull.v1.XmlPullParserFactory

class MainActivity : AppCompatActivity() {

    private lateinit var listLayout: LinearLayout
    private lateinit var speedGraphText: TextView
    private lateinit var speedGraphView: SpeedGraphView
    private val downloadSpeedHistory = mutableListOf<Int>()
    private val uploadSpeedHistory = mutableListOf<Int>()
    private val maxSpeedHistoryPoints = 30
    private val handler = Handler(Looper.getMainLooper())
    private val interval = 3000L
    private val listInterval = 1000L
    private var uiTick = 0
    private var fingerDown = false
    private var fingerDownSince = 0L
    private var uiVisible = true
    private val savePath = "/storage/emulated/0/Download"
    private var selectMode = false
    private val selectedTorrents = mutableSetOf<Int>()
    private var skipMagnetSelection = false
    private var activeFilter = "All"
    private var searchQuery = ""
    private var sortMode = "None"
    private val TORRENT_SORT_MODES = arrayOf("None", "Name (A-Z)", "Name (Z-A)", "Size (Largest First)", "Size (Smallest First)", "Date Added (Newest First)", "Date Added (Oldest First)", "Progress (Highest First)", "Progress (Lowest First)", "Status (A-Z)", "Status (Z-A)")
    private var onlineSearchQueryText = ""
    private var onlineSearchResults: List<TorrentSearchResult> = emptyList()
    private var onlineSearchSortMode = "Seeders"
    private var onlineSearchProviderFilter = "All"
    private var onlineSearchStatus = "Enter a search and tap Search."
    private var currentDetailsTab = ""
    private var currentDetailsTorrentIndex = -1
    private var currentDetailsContentText: TextView? = null
    private var currentDetailsFileListLayout: LinearLayout? = null
    private var filesBuiltForIndex = -1
    private var filesPendingSelection: MutableSet<Int>? = null
    private val filesProgressViews = mutableMapOf<Int, Pair<TextView, ProgressBar>>()
    private val filesPrevProgressSnapshot = mutableMapOf<Int, Pair<Long, Long>>()
    private var networkFeaturesRefreshRunnable: Runnable? = null
    private var isNetworkFeaturesScreenActive = false
    private var connectionRefreshRunnable: Runnable? = null
    private var isConnectionScreenActive = false
    private var storageRefreshRunnable: Runnable? = null
    private var isStorageScreenActive = false
    private var globalStatsRefreshRunnable: Runnable? = null
    private var isGlobalStatsScreenActive = false
    private var rssUiRefreshRunnable: Runnable? = null
    private var isRssScreenActive = false
    private var logUiRefreshRunnable: Runnable? = null
    private var isLogScreenActive = false
    private var isOnMainScreen = false

    private fun bgColor(): Int = Color.parseColor("#F8F9FA")
    private fun cardColor(): Int = Color.WHITE
    private fun currentThemeName(): String = "Light"

    private fun roundedCardBackground(): android.graphics.drawable.GradientDrawable = android.graphics.drawable.GradientDrawable().apply {
        setColor(Color.WHITE)
        cornerRadius = 4f
        setStroke(1, Color.parseColor("#E1E5EA"))
    }

    private val pickTorrent = registerForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        if (uri == null) {
            Toast.makeText(this, "No file selected", Toast.LENGTH_SHORT).show()
            return@registerForActivityResult
        }
        try {
            val filePath = copyTorrentToFiles(uri.toString())
            showTorrentFileSelection(filePath)
        } catch (e: Exception) {
            e.printStackTrace()
            Toast.makeText(this, "Could not read torrent file", Toast.LENGTH_SHORT).show()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        AppLog.init(applicationContext)
        AppLog.info("BitFlow opened")
        val listViewPrefs = torrentListViewPrefs()
        activeFilter = listViewPrefs.getString("filter", "All") ?: "All"
        sortMode = listViewPrefs.getString("sort", "None") ?: "None"
        val serviceIntent = Intent(this, TorrentService::class.java)
        startTorrentService(serviceIntent)
        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (isOnMainScreen) {
                    isEnabled = false
                    onBackPressedDispatcher.onBackPressed()
                    isEnabled = true
                } else showMainScreen()
            }
        })
        showMainScreen()
        startUiUpdates()
        if (savedInstanceState == null) handleIncomingIntent(intent)
        ensureStorageAccess()
        ensureNotificationAccess()
    }

    override fun setContentView(view: android.view.View?) {
        super.setContentView(view)
        isOnMainScreen = false
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        handleIncomingIntent(intent)
    }

    override fun onStart() {
        super.onStart()
        uiVisible = true
        updateTorrentList()
    }

    override fun onStop() {
        uiVisible = false
        super.onStop()
    }

    override fun dispatchTouchEvent(ev: android.view.MotionEvent): Boolean {
        when (ev.actionMasked) {
            android.view.MotionEvent.ACTION_DOWN -> { fingerDown = true; fingerDownSince = System.currentTimeMillis() }
            android.view.MotionEvent.ACTION_UP, android.view.MotionEvent.ACTION_CANCEL -> fingerDown = false
        }
        return super.dispatchTouchEvent(ev)
    }

    override fun onDestroy() {
        stopRssUiRefresh()
        stopLogUiRefresh()
        super.onDestroy()
    }

    private var askedStorageAccess = false

    private fun ensureStorageAccess() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            if (android.os.Environment.isExternalStorageManager() || askedStorageAccess) return
            askedStorageAccess = true
            AlertDialog.Builder(this)
                .setTitle("Allow storage access")
                .setMessage("BitFlow saves downloads to your Download folder. Turn on access for BitFlow, then return to the app.")
                .setCancelable(false)
                .setPositiveButton("Open settings") { _, _ ->
                    try { startActivity(Intent(android.provider.Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION, Uri.parse("package:$packageName"))) }
                    catch (_: Throwable) { try { startActivity(Intent(android.provider.Settings.ACTION_MANAGE_ALL_FILES_ACCESS_PERMISSION)) } catch (_: Throwable) {} }
                }
                .setNegativeButton("Later", null)
                .show()
        } else {
            val readGranted = checkSelfPermission(android.Manifest.permission.READ_EXTERNAL_STORAGE) == android.content.pm.PackageManager.PERMISSION_GRANTED
            val writeGranted = checkSelfPermission(android.Manifest.permission.WRITE_EXTERNAL_STORAGE) == android.content.pm.PackageManager.PERMISSION_GRANTED
            if (!readGranted || !writeGranted) requestPermissions(arrayOf(android.Manifest.permission.READ_EXTERNAL_STORAGE, android.Manifest.permission.WRITE_EXTERNAL_STORAGE), 1001)
        }
    }

    private fun ensureNotificationAccess() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU) return
        if (checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS) != android.content.pm.PackageManager.PERMISSION_GRANTED) requestPermissions(arrayOf(android.Manifest.permission.POST_NOTIFICATIONS), 1002)
    }

    private fun handleIncomingIntent(intent: Intent?) {
        if (intent == null || intent.action != Intent.ACTION_VIEW) return
        val data = intent.data ?: return
        val uriText = data.toString()
        setIntent(Intent(this, MainActivity::class.java))
        if (uriText.startsWith("magnet:")) {
            val hash = extractHashFromMagnetInput(uriText)
            if (isTorrentAlreadyAddedByHash(hash)) { showAlreadyAddedMessage(); return }
            showMagnetMetadataScreen(uriText)
            return
        }
        try {
            val filePath = copyTorrentToFiles(uriText)
            val hash = try { TorrentNative.getTorrentFileHash(filePath) } catch (_: Throwable) { "" }
            if (isTorrentAlreadyAddedByHash(hash)) { showAlreadyAddedMessage(); return }
            showTorrentFileSelection(filePath)
            Toast.makeText(this, "Torrent file opened in BitFlow", Toast.LENGTH_SHORT).show()
        } catch (e: Exception) {
            e.printStackTrace()
            Toast.makeText(this, "Could not open torrent file", Toast.LENGTH_SHORT).show()
        }
    }

    private fun sendTorrentAction(action: String, torrentIndex: Int, deleteFiles: Boolean = false) {
        val intent = Intent(this, TorrentService::class.java)
        intent.putExtra("ACTION", action)
        intent.putExtra("TORRENT_INDEX", torrentIndex)
        intent.putExtra("TORRENT_HASH", getSafeTorrentHashForAction(torrentIndex))
        intent.putExtra("TORRENT_MAGNET", getSafeTorrentMagnetForAction(torrentIndex))
        if (action == "REMOVE_TORRENT") intent.putExtra("DELETE_FILES", deleteFiles)
        startTorrentService(intent)
    }

    private fun showMainScreen() {
        stopNetworkFeaturesAutoRefresh()
        stopStorageAutoRefresh()
        stopGlobalStatsAutoRefresh()
        stopRssUiRefresh()
        stopLogUiRefresh()
        currentDetailsTab = ""
        currentDetailsTorrentIndex = -1
        currentDetailsContentText = null
        currentDetailsFileListLayout = null
        val density = resources.displayMetrics.density
        fun dp(value: Int) = (value * density).toInt()
        val blue = Color.parseColor("#007BFF")
        val dark = Color.parseColor("#343A40")
        val muted = Color.parseColor("#6C757D")
        val light = Color.parseColor("#F8F9FA")
        val white = Color.WHITE
        val border = Color.parseColor("#E1E5EA")
        fun panelBackground() = android.graphics.drawable.GradientDrawable().apply { shape = android.graphics.drawable.GradientDrawable.RECTANGLE; cornerRadius = dp(4).toFloat(); setColor(white); setStroke(dp(1), border) }
        fun fieldBackground() = android.graphics.drawable.GradientDrawable().apply { shape = android.graphics.drawable.GradientDrawable.RECTANGLE; cornerRadius = dp(4).toFloat(); setColor(white); setStroke(dp(1), border) }
        fun styleButton(button: Button, primary: Boolean = false) {
            button.isAllCaps = false
            button.minHeight = dp(44)
            button.setPadding(dp(14), dp(8), dp(14), dp(8))
            button.textSize = 14f
            button.background = android.graphics.drawable.GradientDrawable().apply { shape = android.graphics.drawable.GradientDrawable.RECTANGLE; cornerRadius = dp(4).toFloat(); if (primary) setColor(blue) else { setColor(white); setStroke(dp(1), blue) } }
            button.setTextColor(if (primary) white else blue)
        }
        fun heading(text: String, size: Float = 18f) = TextView(this).apply { this.text = text; textSize = size; setTextColor(dark); setTypeface(typeface, android.graphics.Typeface.BOLD); setPadding(0, dp(8), 0, dp(8)) }
        fun body(text: String) = TextView(this).apply { this.text = text; textSize = 13f; setTextColor(muted); setPadding(0, 0, 0, dp(8)) }
        fun spacer(height: Int = 8) = Space(this).apply { layoutParams = LinearLayout.LayoutParams(1, dp(height)) }

        val root = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setPadding(dp(20), dp(18), dp(20), dp(24)); setBackgroundColor(light) }
        val scroll = ScrollView(this).apply { isFillViewport = true }
        scroll.addView(root)
        val header = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; gravity = android.view.Gravity.CENTER_VERTICAL }
        val logo = ImageView(this).apply { setImageResource(R.drawable.bitflow_logo); scaleType = ImageView.ScaleType.CENTER_INSIDE; layoutParams = LinearLayout.LayoutParams(dp(46), dp(46)).apply { rightMargin = dp(12) } }
        val headerText = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        headerText.addView(TextView(this).apply { text = "BitFlow"; textSize = 25f; setTextColor(dark); setTypeface(typeface, android.graphics.Typeface.BOLD) })
        headerText.addView(TextView(this).apply { text = "Torrent Downloader"; textSize = 13f; setTextColor(muted) })
        header.addView(logo); header.addView(headerText)
        val settings = Button(this).apply { text = "Settings"; styleButton(this); setOnClickListener { showSettingsScreen() } }
        header.addView(settings, LinearLayout.LayoutParams(-2, dp(44)).apply { leftMargin = dp(8) })
        root.addView(header); root.addView(spacer(14))

        val searchBox = EditText(this).apply {
            hint = "Search downloads"; textSize = 14f; setTextColor(dark); setHintTextColor(muted); setSingleLine(true); setText(searchQuery); setSelection(text.length); setPadding(dp(14), 0, dp(14), 0); background = fieldBackground()
            addTextChangedListener(object : TextWatcher { override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}; override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) { searchQuery = s?.toString() ?: ""; updateTorrentList() }; override fun afterTextChanged(s: Editable?) {} })
        }
        root.addView(searchBox, LinearLayout.LayoutParams(-1, dp(48))); root.addView(spacer(10))

        val filterRow = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        fun makeFilterButton(name: String): Button = Button(this).apply { text = name; styleButton(this, activeFilter == name); layoutParams = LinearLayout.LayoutParams(-2, dp(42)).apply { rightMargin = dp(6) }; setOnClickListener { activeFilter = name; torrentListViewPrefs().edit().putString("filter", name).apply(); selectedTorrents.clear(); selectMode = false; showMainScreen() } }
        filterRow.addView(makeFilterButton("All")); filterRow.addView(makeFilterButton("Active")); filterRow.addView(makeFilterButton("Paused")); filterRow.addView(makeFilterButton("Completed"))
        root.addView(horizontalScrollFor(filterRow)); root.addView(spacer(10))

        val downloadHeader = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; gravity = android.view.Gravity.CENTER_VERTICAL }
        downloadHeader.addView(heading("Downloads", 19f), LinearLayout.LayoutParams(0, -2, 1f))
        val sortButton = Button(this).apply { text = "Sort"; styleButton(this); setOnClickListener { AlertDialog.Builder(this@MainActivity).setTitle("Sort torrents by").setItems(TORRENT_SORT_MODES) { _, which -> sortMode = TORRENT_SORT_MODES[which]; torrentListViewPrefs().edit().putString("sort", sortMode).apply(); showMainScreen() }.show() } }
        downloadHeader.addView(sortButton, LinearLayout.LayoutParams(-2, dp(44))); root.addView(downloadHeader)

        val selectRow = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        val selectButton = Button(this).apply { text = if (selectMode) "Done" else "Select"; styleButton(this, selectMode); setOnClickListener { selectMode = !selectMode; selectedTorrents.clear(); showMainScreen() } }
        selectRow.addView(selectButton, LinearLayout.LayoutParams(0, dp(42), 1f).apply { rightMargin = dp(6) })
        val selectAll = Button(this).apply { text = "Select all"; styleButton(this); isEnabled = selectMode; setOnClickListener { if (selectMode) { selectedTorrents.clear(); selectedTorrents.addAll(getVisibleTorrentIndexes()); updateTorrentList() } } }
        selectRow.addView(selectAll, LinearLayout.LayoutParams(0, dp(42), 1f)); root.addView(selectRow)
        if (selectMode) {
            val bulkRow = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
            fun bulkButton(label: String, action: () -> Unit) = Button(this).apply { text = label; styleButton(this); setOnClickListener { action() } }
            bulkRow.addView(bulkButton("Pause") { selectedTorrents.forEach { sendTorrentAction("PAUSE_TORRENT", it) }; selectedTorrents.clear(); selectMode = false; showMainScreen() }, LinearLayout.LayoutParams(0, dp(42), 1f).apply { rightMargin = dp(6) })
            bulkRow.addView(bulkButton("Resume") { selectedTorrents.forEach { sendTorrentAction("RESUME_TORRENT", it) }; selectedTorrents.clear(); selectMode = false; showMainScreen() }, LinearLayout.LayoutParams(0, dp(42), 1f).apply { rightMargin = dp(6) })
            bulkRow.addView(bulkButton("Recheck") { selectedTorrents.forEach { TorrentNative.forceRecheck(it) }; selectedTorrents.clear(); selectMode = false; showMainScreen() }, LinearLayout.LayoutParams(0, dp(42), 1f)); root.addView(bulkRow)
        }
        listLayout = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setPadding(0, dp(8), 0, dp(80)) }
        root.addView(listLayout)

        val addButton = Button(this).apply { text = "+  Add download"; styleButton(this, true); textSize = 15f; setOnClickListener { showAddDownloadDialog() } }
        root.addView(addButton, LinearLayout.LayoutParams(-1, dp(50)).apply { topMargin = dp(8) })
        setContentView(scroll)
        isOnMainScreen = true
        updateTorrentList()
    }

    private fun showAddDownloadDialog() {
        val density = resources.displayMetrics.density
        fun dp(v: Int) = (v * density).toInt()
        val box = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setPadding(dp(20), dp(8), dp(20), dp(8)) }
        val input = EditText(this).apply { hint = "Magnet link or info hash"; setSingleLine(true) }
        box.addView(input, LinearLayout.LayoutParams(-1, dp(50)))
        val dialog = AlertDialog.Builder(this).setTitle("Add download").setView(box).setNegativeButton("Cancel", null).create()
        dialog.setButton(AlertDialog.BUTTON_POSITIVE, "Add Magnet") { _, _ ->
            var magnet = input.text.toString().trim()
            if (magnet.isEmpty()) { Toast.makeText(this, "Enter a magnet link or hash", Toast.LENGTH_SHORT).show(); return@setButton }
            if (!magnet.startsWith("magnet:")) magnet = "magnet:?xt=urn:btih:$magnet"
            val hash = extractHashFromMagnetInput(magnet)
            if (isTorrentAlreadyAddedByHash(hash)) showAlreadyAddedMessage() else showMagnetMetadataScreen(magnet)
        }
        dialog.show()
        dialog.setButton(AlertDialog.BUTTON_NEUTRAL, "Choose .torrent") { _, _ -> pickTorrent.launch("*/*") }
    }

    private fun showSettingsScreen() {
        val density = resources.displayMetrics.density
        fun dp(v: Int) = (v * density).toInt()
        val dark = Color.parseColor("#343A40"); val muted = Color.parseColor("#6C757D"); val light = Color.parseColor("#F8F9FA"); val border = Color.parseColor("#E1E5EA")
        fun card(title: String, subtitle: String, click: () -> Unit): LinearLayout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL; setPadding(dp(16), dp(14), dp(16), dp(14)); background = android.graphics.drawable.GradientDrawable().apply { setColor(Color.WHITE); cornerRadius = dp(4).toFloat(); setStroke(dp(1), border) }; isClickable = true; setOnClickListener { click() }
            addView(TextView(this@MainActivity).apply { text = title; textSize = 16f; setTextColor(dark); setTypeface(typeface, android.graphics.Typeface.BOLD) })
            addView(TextView(this@MainActivity).apply { text = subtitle; textSize = 13f; setTextColor(muted); setPadding(0, dp(4), 0, 0) })
        }
        val root = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setPadding(dp(20), dp(18), dp(20), dp(24)); setBackgroundColor(light) }
        val scroll = ScrollView(this).apply { isFillViewport = true; addView(root) }
        val header = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; gravity = android.view.Gravity.CENTER_VERTICAL }
        val back = Button(this).apply { text = "Back"; setOnClickListener { showMainScreen() } }
        header.addView(back, LinearLayout.LayoutParams(-2, dp(44)))
        header.addView(TextView(this).apply { text = "Settings"; textSize = 23f; setTextColor(dark); setTypeface(typeface, android.graphics.Typeface.BOLD); setPadding(dp(12), 0, 0, 0) })
        root.addView(header); root.addView(Space(this).apply { layoutParams = LinearLayout.LayoutParams(1, dp(16)) })
        root.addView(TextView(this).apply { text = "Downloads"; textSize = 13f; setTextColor(muted); setPadding(0, dp(8), 0, dp(8)) })
        root.addView(card("Save location", "Choose where downloaded files are stored") { showSaveFolderScreen() }); root.addView(Space(this).apply { layoutParams = LinearLayout.LayoutParams(1, dp(8)) })
        root.addView(card("Speed limits", "Control download and upload limits") { showSpeedLimitsScreen() }); root.addView(Space(this).apply { layoutParams = LinearLayout.LayoutParams(1, dp(8)) })
        root.addView(TextView(this).apply { text = "Network"; textSize = 13f; setTextColor(muted); setPadding(0, dp(12), 0, dp(8)) })
        root.addView(card("Connection", "Connection status and torrent networking") { showConnectionScreen() }); root.addView(Space(this).apply { layoutParams = LinearLayout.LayoutParams(1, dp(8)) })
        root.addView(card("Network features", "Port forwarding and network options") { showNetworkFeaturesScreen() }); root.addView(Space(this).apply { layoutParams = LinearLayout.LayoutParams(1, dp(8)) })
        root.addView(TextView(this).apply { text = "Discovery"; textSize = 13f; setTextColor(muted); setPadding(0, dp(12), 0, dp(8)) })
        root.addView(card("Online search", "Search torrent providers") { showOnlineSearchScreen() }); root.addView(Space(this).apply { layoutParams = LinearLayout.LayoutParams(1, dp(8)) })
        root.addView(card("RSS feeds", "Manage RSS subscriptions") { showRssScreen() }); root.addView(Space(this).apply { layoutParams = LinearLayout.LayoutParams(1, dp(8)) })
        root.addView(TextView(this).apply { text = "Diagnostics"; textSize = 13f; setTextColor(muted); setPadding(0, dp(12), 0, dp(8)) })
        root.addView(card("Statistics", "Transfer activity and torrent statistics") { showGlobalStatsScreen() }); root.addView(Space(this).apply { layoutParams = LinearLayout.LayoutParams(1, dp(8)) })
        root.addView(card("Execution log", "View BitFlow activity and errors") { showExecutionLogScreen() }); root.addView(Space(this).apply { layoutParams = LinearLayout.LayoutParams(1, dp(8)) })
        root.addView(card("Storage", "View available storage") { showStorageScreen() }); root.addView(Space(this).apply { layoutParams = LinearLayout.LayoutParams(1, dp(8)) })
        root.addView(TextView(this).apply { text = "About"; textSize = 13f; setTextColor(muted); setPadding(0, dp(12), 0, dp(8)) })
        root.addView(card("BitFlow", "Torrent Downloader • Version 1.0.0") { showAboutDialog() })
        setContentView(scroll)
    }

    private fun showAboutDialog() {
        AlertDialog.Builder(this).setTitle("BitFlow").setMessage("BitFlow: Torrent Downloader\nVersion 1.0.0\n\nFast, simple torrent downloading for Android.").setPositiveButton("OK", null).show()
    }
