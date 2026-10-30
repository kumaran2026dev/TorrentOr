package com.example.torrentor

import android.content.Context
import android.graphics.Color
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.os.StatFs
import android.view.Gravity
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

private fun AppCompatActivity.bitFlowSettingsRoot(title: String): LinearLayout {
    val root = LinearLayout(this).apply {
        orientation = LinearLayout.VERTICAL
        setPadding(32, 32, 32, 32)
        setBackgroundColor(Color.parseColor("#F6F7F9"))
    }
    root.addView(TextView(this).apply {
        text = title
        textSize = 24f
        setTextColor(Color.parseColor("#202124"))
        setTypeface(typeface, android.graphics.Typeface.BOLD)
        setPadding(0, 0, 0, 20)
    })
    return root
}

private fun AppCompatActivity.bitFlowSettingsButton(textValue: String, action: () -> Unit): Button = Button(this).apply {
    text = textValue
    isAllCaps = false
    textSize = 15f
    gravity = Gravity.START or Gravity.CENTER_VERTICAL
    setOnClickListener { action() }
}

private fun AppCompatActivity.bitFlowBackButton(): Button = Button(this).apply {
    text = "Back"
    isAllCaps = false
    setOnClickListener { onBackPressedDispatcher.onBackPressed() }
}

fun MainActivity.showConnectionScreen() {
    val root = bitFlowSettingsRoot("Network · Connection")
    val status = TextView(this).apply {
        textSize = 16f
        setTextColor(Color.parseColor("#374151"))
        setPadding(0, 0, 0, 16)
    }
    val connectivity = getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
    fun refresh() {
        val network = connectivity.activeNetwork
        val caps = network?.let { connectivity.getNetworkCapabilities(it) }
        val connected = caps != null
        val type = when {
            caps?.hasTransport(NetworkCapabilities.TRANSPORT_WIFI) == true -> "Wi-Fi"
            caps?.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR) == true -> "Mobile data"
            caps?.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET) == true -> "Ethernet"
            connected -> "Other network"
            else -> "Offline"
        }
        status.text = "Status: ${if (connected) "Connected" else "Disconnected"}\nNetwork: $type"
    }
    root.addView(status)
    root.addView(bitFlowSettingsButton("Refresh") { refresh() })
    root.addView(bitFlowBackButton())
    refresh()
    setContentView(ScrollView(this).apply { addView(root) })
}

fun MainActivity.showGlobalStatsScreen() {
    val root = bitFlowSettingsRoot("Diagnostics · Statistics")
    val stats = TextView(this).apply {
        textSize = 15f
        setTextColor(Color.parseColor("#374151"))
        setPadding(0, 0, 0, 16)
    }
    fun refresh() {
        stats.text = "BitFlow statistics\n\n" +
                "UI status: Running\n" +
                "Application: BitFlow: Torrent Downloader\n" +
                "Package: $packageName\n\n" +
                "Use the Downloads screen for live torrent progress, speed and ETA."
    }
    root.addView(stats)
    root.addView(bitFlowSettingsButton("Refresh") { refresh() })
    root.addView(bitFlowBackButton())
    refresh()
    setContentView(ScrollView(this).apply { addView(root) })
}

fun MainActivity.showStorageScreen() {
    val root = bitFlowSettingsRoot("Diagnostics · Storage")
    val info = TextView(this).apply {
        textSize = 15f
        setTextColor(Color.parseColor("#374151"))
        setPadding(0, 0, 0, 16)
    }
    fun formatBytes(value: Long): String {
        if (value < 1024L) return "$value B"
        if (value < 1024L * 1024L) return "%.1f KB".format(value / 1024.0)
        if (value < 1024L * 1024L * 1024L) return "%.1f MB".format(value / (1024.0 * 1024.0))
        return "%.1f GB".format(value / (1024.0 * 1024.0 * 1024.0))
    }
    fun refresh() {
        val stat = StatFs(android.os.Environment.getExternalStorageDirectory().path)
        val total = stat.blockCountLong * stat.blockSizeLong
        val free = stat.availableBlocksLong * stat.blockSizeLong
        val used = total - free
        info.text = "Device storage\n\n" +
                "Total: ${formatBytes(total)}\n" +
                "Used: ${formatBytes(used)}\n" +
                "Available: ${formatBytes(free)}\n\n" +
                "Default download folder:\n/storage/emulated/0/Download"
    }
    root.addView(info)
    root.addView(bitFlowSettingsButton("Refresh") { refresh() })
    root.addView(bitFlowBackButton())
    refresh()
    setContentView(ScrollView(this).apply { addView(root) })
}
