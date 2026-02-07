package com.smartmeal.app

import android.os.Bundle
import android.util.Log
import android.widget.ArrayAdapter
import android.widget.Button
import android.widget.Spinner
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import okhttp3.Call
import okhttp3.Callback
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response
import org.json.JSONObject
import java.io.IOException
import java.util.concurrent.TimeUnit

class MainActivity : AppCompatActivity() {

    private lateinit var serverUrl: android.widget.EditText
    private lateinit var dailyTotal: TextView
    private lateinit var refresh: Button
    private lateinit var foodSpinner: Spinner
    private lateinit var weightInput: android.widget.EditText
    private lateinit var addMeal: Button
    private lateinit var status: TextView

    private val client = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(10, TimeUnit.SECONDS)
        .build()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        serverUrl = findViewById(R.id.serverUrl)
        dailyTotal = findViewById(R.id.dailyTotal)
        refresh = findViewById(R.id.refresh)
        foodSpinner = findViewById(R.id.foodSpinner)
        weightInput = findViewById(R.id.weightInput)
        addMeal = findViewById(R.id.addMeal)
        status = findViewById(R.id.status)

        // Default: emulator use 10.0.2.2 for host machine; replace with your PC's LAN IP on device
        serverUrl.setText("http://10.0.2.2:5000")

        refresh.setOnClickListener { fetchDaily(); loadFoods() }
        addMeal.setOnClickListener { postMeal() }

        loadFoods()
        fetchDaily()
    }

    private fun baseUrl(): String {
        var url = serverUrl.text.toString().trim()
        if (!url.startsWith("http")) url = "http://$url"
        return url.trimEnd('/')
    }

    private fun loadFoods() {
        val request = Request.Builder().url("${baseUrl()}/api/foods").build()
        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                runOnUiThread {
                    status.text = "Cannot reach server. Check URL and network."
                    Log.e(TAG, "api/foods", e)
                }
            }
            override fun onResponse(call: Call, response: Response) {
                if (!response.isSuccessful) {
                    runOnUiThread { status.text = "Server error: ${response.code}" }
                    return
                }
                val body = response.body?.string() ?: return
                try {
                    val arr = JSONObject(body).getJSONArray("foods")
                    val list = (0 until arr.length()).map { arr.getString(it) }
                    runOnUiThread {
                        val adapter = ArrayAdapter(
                            this@MainActivity,
                            android.R.layout.simple_spinner_dropdown_item,
                            list
                        )
                        foodSpinner.adapter = adapter
                        if (list.isNotEmpty()) status.text = "Ready. ${list.size} foods loaded."
                    }
                } catch (e: Exception) {
                    runOnUiThread { status.text = "Parse error: ${e.message}" }
                }
            }
        })
    }

    private fun fetchDaily() {
        val request = Request.Builder().url("${baseUrl()}/api/daily").build()
        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                runOnUiThread {
                    dailyTotal.text = "Daily total: -- kcal"
                    status.text = "Cannot reach server."
                }
            }
            override fun onResponse(call: Call, response: Response) {
                if (!response.isSuccessful) {
                    runOnUiThread { dailyTotal.text = "Daily total: -- kcal" }
                    return
                }
                val body = response.body?.string() ?: return
                try {
                    val total = JSONObject(body).optDouble("daily_total_calories", 0.0).toInt()
                    runOnUiThread { dailyTotal.text = "Daily total: $total kcal" }
                } catch (_: Exception) {}
            }
        })
    }

    private fun postMeal() {
        val foodId = foodSpinner.selectedItem?.toString() ?: ""
        if (foodId.isEmpty()) {
            Toast.makeText(this, "Load foods first and select one", Toast.LENGTH_SHORT).show()
            return
        }
        val weightStr = weightInput.text.toString().trim()
        val json = JSONObject().apply {
            put("food_id", foodId)
            if (weightStr.isNotEmpty()) put("weight_g", weightStr.toDoubleOrNull() ?: 100)
        }
        val body = json.toString().toRequestBody("application/json".toMediaType())
        val request = Request.Builder()
            .url("${baseUrl()}/api/meal")
            .post(body)
            .build()
        status.text = "Sending…"
        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                runOnUiThread {
                    status.text = "Failed: ${e.message}"
                    Toast.makeText(this@MainActivity, "Network error", Toast.LENGTH_SHORT).show()
                }
            }
            override fun onResponse(call: Call, response: Response) {
                val msg = response.body?.string() ?: ""
                runOnUiThread {
                    if (response.isSuccessful) {
                        try {
                            val obj = JSONObject(msg)
                            val total = obj.optInt("daily_total_calories", 0)
                            dailyTotal.text = "Daily total: $total kcal"
                            status.text = "Added: ${obj.optString("food", "")}"
                            Toast.makeText(this@MainActivity, "Meal added", Toast.LENGTH_SHORT).show()
                        } catch (_: Exception) {
                            status.text = "Meal added."
                            fetchDaily()
                        }
                    } else {
                        status.text = "Error: ${response.code} $msg"
                        Toast.makeText(this@MainActivity, "Add meal failed", Toast.LENGTH_SHORT).show()
                    }
                }
            }
        })
    }

    companion object {
        private const val TAG = "SmartMeal"
    }
}
