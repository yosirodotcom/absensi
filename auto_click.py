import http.server
import socketserver
import json
import threading
import time
from datetime import datetime
import schedule
import webbrowser
import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- App State ---
state = {
    'is_running': False,
    'in_time': '07:30',
    'out_time': '16:00',
    'selected_dates': []
}

# --- Selenium Automation ---
def perform_automation():
    today_str = datetime.now().strftime('%Y-%m-%d')
    if today_str not in state.get('selected_dates', []):
        print(f"[{time.strftime('%H:%M:%S')}] Skipping automation: Today ({today_str}) is not selected.")
        return
        
    print(f"[{time.strftime('%H:%M:%S')}] Attempting automation...")
    try:
        options = webdriver.ChromeOptions()
        driver = webdriver.Chrome(options=options)
        
        print("1. Opening login page...")
        driver.get("https://intradikti.kemdiktisaintek.go.id/login")
        
        time.sleep(3)
        
        print("2. Entering NIP...")
        nip_input = driver.find_element(By.NAME, "nip")
        nip_input.send_keys("198202032005011003")
        
        print("3. Entering Password...")
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys("Pontianak&46")
        
        print("4. Clicking 'Masuk' button...")
        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        
        print("5. Waiting for login to complete and dashboard to load...")
        time.sleep(5)
            
        print("6. Navigating directly to Presensi page...")
        driver.get("https://intradikti.kemdiktisaintek.go.id/presensi/")
            
        print("7. Waiting for first 'Rekam Kehadiran' button...")
        rekam_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Rekam Kehadiran')]"))
        )
        
        print("8. Clicking first 'Rekam Kehadiran' button...")
        driver.execute_script("arguments[0].click();", rekam_button)
        
        print("9. Waiting 15 seconds for modal to load and verify location...")
        time.sleep(15)
        
        print("10. Clicking the second 'Rekam Kehadiran' button inside the modal...")
        final_rekam_button = WebDriverWait(driver, 15).until(
            lambda d: d.execute_script(
                "const btn = Array.from(document.querySelectorAll('button')).find(b => b.getAttribute('wire:target') === 'clock');"
                "return (btn && !btn.disabled) ? btn : null;"
            )
        )
        driver.execute_script("arguments[0].click();", final_rekam_button)
        
        print("Presensi sequence completed successfully!")
        print("Waiting 1 minute before closing...")
        time.sleep(60)
        
        driver.quit()
        print("Browser closed.")
        
    except Exception as e:
        print(f"Automation error: {e}")


# --- Web UI Backend ---
HTML_PAGE = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" name="viewport"/>
<title>Auto Presensi</title>
<!-- BEGIN: Tailwind CSS and Plugins -->
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<!-- END: Tailwind CSS and Plugins -->
<!-- BEGIN: Custom Styling -->
<style data-purpose="custom-gradient">
    .bg-main-gradient {
      background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    }
    .timer-glow {
      box-shadow: 0 0 20px rgba(34, 197, 94, 0.2);
    }
  </style>
<style data-purpose="mobile-adjustments">
    body {
      -webkit-tap-highlight-color: transparent;
      user-select: none;
      -webkit-user-select: none;
    }
    
    /* Scroll Snapping for the Custom Time Pickers */
    .time-wheel {
       scroll-snap-type: y mandatory;
       scrollbar-width: none; /* Firefox */
       -ms-overflow-style: none; /* IE/Edge */
    }
    .time-wheel::-webkit-scrollbar {
       display: none; /* Chrome/Safari */
    }
    
    /* Hide scrollbar for horizontal lists */
    .scrollbar-hide::-webkit-scrollbar { display: none; }
    .scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
    .time-wheel-item {
       scroll-snap-align: center;
       height: 48px;
       line-height: 48px;
    }
    
    /* Overlay to fade top/bottom of the wheel */
    .wheel-overlay {
       background: linear-gradient(180deg, rgba(30,41,59,1) 0%, rgba(30,41,59,0) 30%, rgba(30,41,59,0) 70%, rgba(30,41,59,1) 100%);
       pointer-events: none;
    }
  </style>
</head>
<body class="bg-main-gradient text-slate-100 min-h-screen flex flex-col font-sans">
<!-- BEGIN: Main App Container -->
<main class="flex-1 flex flex-col p-6 max-w-md mx-auto w-full" data-purpose="app-interface">
<!-- BEGIN: Header Section -->
<header class="pt-4 pb-4 text-center" data-purpose="header">
<h1 class="text-2xl font-bold tracking-tight text-emerald-500">Auto Presensi</h1>
<p class="text-slate-400 text-sm mt-1">Automated Attendance Tracker</p>
</header>
<!-- END: Header Section -->
<!-- BEGIN: Date Selection -->
<section class="mb-5 flex flex-col" data-purpose="date-selector">
    <div class="flex items-center justify-between mb-2 px-1">
        <label class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Active Dates</label>
        <button id="select-weekdays" class="text-xs text-emerald-500 font-bold hover:text-emerald-400 transition-colors uppercase tracking-wider">Select Weekdays</button>
    </div>
    <div id="date-list" class="flex overflow-x-auto space-x-3 pb-2 scrollbar-hide" style="scroll-snap-type: x mandatory;">
        <!-- Generated by JS -->
    </div>
</section>
<!-- END: Date Selection -->
<!-- BEGIN: Custom Time Configuration -->
<section class="grid grid-cols-2 gap-4 mb-6" data-purpose="time-inputs">
    
    <!-- IN Time Custom Wheel -->
    <div class="flex flex-col items-center bg-slate-800/50 border border-slate-700 rounded-2xl py-3 relative overflow-hidden" id="in-time-container">
        <label class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 z-10">IN TIME</label>
        <div class="flex space-x-2 text-2xl font-bold text-emerald-400 h-[144px] relative w-full justify-center">
            
            <!-- Hour Wheel -->
            <div id="in-h" class="time-wheel overflow-y-scroll h-full text-center relative z-0 w-12" onscroll="updateWheelStyle(this)">
                <!-- Spacer items -->
                <div class="time-wheel-item"></div>
                <!-- 00-23 Generated by JS -->
            </div>
            
            <div class="flex items-center justify-center font-bold text-slate-500 z-10">:</div>
            
            <!-- Minute Wheel -->
            <div id="in-m" class="time-wheel overflow-y-scroll h-full text-center relative z-0 w-12" onscroll="updateWheelStyle(this)">
                <!-- Spacer items -->
                <div class="time-wheel-item"></div>
                <!-- 00-59 Generated by JS -->
            </div>
            
            <!-- Fade Overlay -->
            <div class="absolute inset-0 wheel-overlay z-10"></div>
            <!-- Selection Highlight Line -->
            <div class="absolute top-[48px] left-0 right-0 h-[48px] border-y border-emerald-500/30 z-0 pointer-events-none bg-emerald-500/5"></div>
        </div>
    </div>
    
    <!-- OUT Time Custom Wheel -->
    <div class="flex flex-col items-center bg-slate-800/50 border border-slate-700 rounded-2xl py-3 relative overflow-hidden" id="out-time-container">
        <label class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 z-10">OUT TIME</label>
        <div class="flex space-x-2 text-2xl font-bold text-emerald-400 h-[144px] relative w-full justify-center">
            
            <!-- Hour Wheel -->
            <div id="out-h" class="time-wheel overflow-y-scroll h-full text-center relative z-0 w-12" onscroll="updateWheelStyle(this)">
                <div class="time-wheel-item"></div>
            </div>
            
            <div class="flex items-center justify-center font-bold text-slate-500 z-10">:</div>
            
            <!-- Minute Wheel -->
            <div id="out-m" class="time-wheel overflow-y-scroll h-full text-center relative z-0 w-12" onscroll="updateWheelStyle(this)">
                <div class="time-wheel-item"></div>
            </div>
            
            <div class="absolute inset-0 wheel-overlay z-10"></div>
            <div class="absolute top-[48px] left-0 right-0 h-[48px] border-y border-emerald-500/30 z-0 pointer-events-none bg-emerald-500/5"></div>
        </div>
    </div>
    
</section>
<!-- END: Custom Time Configuration -->
<!-- BEGIN: Central Countdown -->
<section class="flex-1 flex flex-col items-center justify-center py-2" data-purpose="countdown-display">
<!-- Circular Progress Visualizer -->
<div class="relative w-56 h-56 flex items-center justify-center">
<!-- Background Circle -->
<svg class="absolute inset-0 w-full h-full -rotate-90">
<circle class="text-slate-800" cx="112" cy="112" fill="transparent" r="95" stroke="currentColor" stroke-width="8"></circle>
<!-- Progress Stroke 2*pi*r -> 2*3.14*95 = 597 -->
<circle class="text-emerald-500 timer-glow transition-all duration-1000 ease-linear" id="progress-circle" cx="112" cy="112" fill="transparent" r="95" stroke="currentColor" stroke-dasharray="597" stroke-dashoffset="597" stroke-linecap="round" stroke-width="8"></circle>
</svg>
<!-- Timer Text -->
<div class="text-center z-10">
<span class="block text-3xl font-mono font-bold tracking-tighter" id="countdown-timer">--:--:--</span>
<span class="block text-[10px] text-slate-500 uppercase font-bold mt-2 tracking-[0.2em]">Next Auto Click</span>
</div>
</div>
</section>
<!-- END: Central Countdown -->
<!-- BEGIN: Action Controls -->
<footer class="pb-6 pt-2 text-center" data-purpose="controls">
<button class="w-full bg-emerald-600 hover:bg-emerald-500 active:scale-[0.98] text-white font-bold py-5 rounded-2xl shadow-lg shadow-emerald-900/20 transition-all duration-200 text-lg uppercase tracking-widest" id="btn-activate" type="button">
        Activate
      </button>
<div class="flex items-center justify-center mt-6">
  <span id="status-dot" class="inline-block w-2 h-2 rounded-full bg-slate-500 mr-2"></span>
  <span id="status-text" class="text-slate-500 text-xs uppercase font-bold tracking-widest">System Standby</span>
</div>
<button id="btn-test" class="text-xs text-slate-600 underline mt-4 hover:text-slate-400">Test Run Bot Now (Hidden)</button>
</footer>
<!-- END: Action Controls -->
</main>
<!-- END: Main App Container -->

<!-- BEGIN: Logic Handlers -->
<script data-purpose="ui-interactions">
    let isActive = false;
    
    // UI Elements
    const activateBtn = document.getElementById('btn-activate');
    const countdownTimerText = document.getElementById('countdown-timer');
    const statusText = document.getElementById('status-text');
    const statusDot = document.getElementById('status-dot');
    const progressCircle = document.getElementById('progress-circle');
    const testBtn = document.getElementById('btn-test');
    
    // --- Date Picker Logic ---
    const dateList = document.getElementById('date-list');
    let selectedDates = []; 
    
    // --- Date Drag & Scroll functionality ---
    let isDraggingDate = false;
    let startXDate = 0;
    let scrollLeftDate = 0;
    let draggedAmountDate = 0;
    
    dateList.style.cursor = 'grab';
    dateList.addEventListener('pointerdown', (e) => {
        if(isActive) return;
        isDraggingDate = true;
        draggedAmountDate = 0;
        dateList.style.cursor = 'grabbing';
        dateList.style.scrollSnapType = 'none';
        dateList.style.scrollBehavior = 'auto';
        startXDate = e.pageX - dateList.offsetLeft;
        scrollLeftDate = dateList.scrollLeft;
        e.preventDefault();
    });
    
    const endDragDate = () => {
        if(!isDraggingDate) return;
        isDraggingDate = false;
        dateList.style.cursor = 'grab';
        dateList.style.scrollSnapType = 'x mandatory';
        dateList.style.scrollBehavior = 'smooth';
    };
    
    dateList.addEventListener('pointerleave', endDragDate);
    dateList.addEventListener('pointerup', endDragDate);
    
    dateList.addEventListener('pointermove', (e) => {
        if(!isDraggingDate || isActive) return;
        e.preventDefault();
        const x = e.pageX - dateList.offsetLeft;
        const walk = (x - startXDate) * 1.5;
        dateList.scrollLeft = scrollLeftDate - walk;
        draggedAmountDate += Math.abs(walk);
    });
    
    dateList.addEventListener('wheel', (e) => {
        if (isActive) return;
        e.preventDefault();
        // Allow using the scroll wheel over the dates to scroll left/right
        dateList.scrollBy({ left: e.deltaY > 0 ? 100 : -100, behavior: 'smooth' });
    });
    
    
    function populateDates() {
        const today = new Date();
        let html = '';
        const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        
        for (let i = 0; i < 30; i++) {
            const d = new Date(today);
            d.setDate(today.getDate() + i);
            
            const y = d.getFullYear();
            const m = String(d.getMonth() + 1).padStart(2, '0');
            const day = String(d.getDate()).padStart(2, '0');
            const dStr = `${y}-${m}-${day}`;
            
            const dayName = dayNames[d.getDay()];
            const dateNum = d.getDate();
            
            html += `
            <div class="flex-shrink-0 w-16 h-20 rounded-xl border border-slate-700 bg-slate-800/50 flex flex-col items-center justify-center cursor-pointer transition-all duration-200 select-none date-item" data-date="${dStr}" onclick="toggleDate('${dStr}')" style="scroll-snap-align: start;">
                <span class="text-xs font-bold text-slate-400 mb-1 pointer-events-none">${dayName}</span>
                <span class="text-xl font-bold text-slate-300 pointer-events-none">${dateNum}</span>
            </div>
            `;
        }
        dateList.innerHTML = html;
        
        // Select today by default if nothing is selected yet
        const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
        selectedDates.push(todayStr);
    }
    
    function toggleDate(dStr) {
        if (isActive || draggedAmountDate > 5) return;
        const idx = selectedDates.indexOf(dStr);
        if (idx > -1) {
            selectedDates.splice(idx, 1);
        } else {
            selectedDates.push(dStr);
        }
        updateDateStyles();
    }
    
    function updateDateStyles() {
        const items = document.querySelectorAll('.date-item');
        items.forEach(item => {
            const dStr = item.getAttribute('data-date');
            const daySpan = item.querySelector('span:nth-child(1)');
            const numSpan = item.querySelector('span:nth-child(2)');
            
            if (selectedDates.includes(dStr)) {
                item.classList.replace('bg-slate-800/50', 'bg-emerald-500/20');
                item.classList.replace('border-slate-700', 'border-emerald-500');
                daySpan.classList.replace('text-slate-400', 'text-emerald-400');
                numSpan.classList.replace('text-slate-300', 'text-emerald-400');
            } else {
                item.classList.replace('bg-emerald-500/20', 'bg-slate-800/50');
                item.classList.replace('border-emerald-500', 'border-slate-700');
                daySpan.classList.replace('text-emerald-400', 'text-slate-400');
                numSpan.classList.replace('text-emerald-400', 'text-slate-300');
            }
            
            if (isActive) {
                item.classList.add('opacity-50', 'cursor-default');
                item.classList.remove('cursor-pointer');
            } else {
                item.classList.remove('opacity-50', 'cursor-default');
                item.classList.add('cursor-pointer');
            }
        });
    }

    document.getElementById('select-weekdays').addEventListener('click', () => {
        if(isActive) return;
        selectedDates = [];
        const items = document.querySelectorAll('.date-item');
        items.forEach(item => {
            const dStr = item.getAttribute('data-date');
            const d = new Date(dStr);
            if(d.getDay() !== 0 && d.getDay() !== 6) {
                selectedDates.push(dStr);
            }
        });
        updateDateStyles();
    });

    populateDates();
    updateDateStyles();
    
    // DOM Elements for Time Wheels
    const inH = document.getElementById('in-h');
    const inM = document.getElementById('in-m');
    const outH = document.getElementById('out-h');
    const outM = document.getElementById('out-m');
    const wheelContainers = [inH, inM, outH, outM];
    
    // Generate Wheel Items
    function populateWheel(container, max) {
        let html = '<div class="time-wheel-item"></div>'; // Top spacer
        for(let i=0; i<=max; i++) {
            const val = i.toString().padStart(2, '0');
            // Adding a distinct class for items so we can identify them later if needed
            html += `<div class="time-wheel-item transition-all duration-200 text-slate-500 cursor-pointer select-none" data-val="${val}" onclick="handleItemClick(this, '${val}')">${val}</div>`;
        }
        html += '<div class="time-wheel-item"></div>'; // Bottom spacer
        container.innerHTML = html;
    }
    
    populateWheel(inH, 23);
    populateWheel(outH, 23);
    populateWheel(inM, 59);
    populateWheel(outM, 59);
    
    // --- Mouse Drag and Swipe Functionality --- //
    let isDragging = false;
    let startY = 0;
    let scrollTop = 0;
    let draggedAmount = 0;
    
    wheelContainers.forEach(container => {
        container.style.cursor = 'grab';
        
        container.addEventListener('pointerdown', (e) => {
            if(isActive) return;
            isDragging = true;
            draggedAmount = 0;
            container.style.cursor = 'grabbing';
            // Disable scroll snap while swiping so it feels fluid
            container.style.scrollSnapType = 'none';
            container.style.scrollBehavior = 'auto'; // Instant during drag for 1:1 feel
            startY = e.pageY - container.offsetTop;
            scrollTop = container.scrollTop;
            e.preventDefault(); // Stop text selection
        });
        
        container.addEventListener('pointerleave', () => {
             endDrag(container);
        });
        
        container.addEventListener('pointerup', () => {
             endDrag(container);
        });
        
        container.addEventListener('pointermove', (e) => {
            if(!isDragging || isActive) return;
            e.preventDefault();
            const y = e.pageY - container.offsetTop;
            const walk = (y - startY) * 1.5; // Multiply by 1.5 for slightly faster swipe
            container.scrollTop = scrollTop - walk;
            draggedAmount += Math.abs(walk);
        });
    });
    
    function endDrag(container) {
        if(!isDragging) return;
        isDragging = false;
        container.style.cursor = 'grab';
        // Re-enable smooth snapping to slide perfectly into place after we let go of the mouse
        container.style.scrollSnapType = 'y mandatory';
        container.style.scrollBehavior = 'smooth';
        
        // Force evaluation of the nearest snap point immediately
        updateWheelStyle(container);
    }
    
    // Wrap the click handler to ignore it if we were just dragging
    function handleItemClick(element, val) {
        if(draggedAmount > 5) return; // Ignore click it was a drag operation!
        setWheelValue(element.parentElement, val);
    }
    // --- End Drag Functionality --- //
    
    // Update styling based on scroll position safely
    function updateWheelStyle(container) {
       if(isActive) return; // Don't style if disabled/locked
       
       const items = container.querySelectorAll('.time-wheel-item[data-val]');
       const scrollTop = container.scrollTop;
       const itemHeight = 48;
       const selectedIndex = Math.round(scrollTop / itemHeight);
       
       items.forEach((item, index) => {
           if(index === selectedIndex) {
               item.classList.remove('text-slate-500', 'scale-75', 'opacity-50');
               item.classList.add('text-emerald-400', 'scale-110', 'opacity-100');
           } else {
               item.classList.remove('text-emerald-400', 'scale-110', 'opacity-100');
               item.classList.add('text-slate-500', 'scale-75', 'opacity-50');
           }
       });
    }

    // Getting and Setting time helper functions
    function setWheelValue(container, valStr) {
        if(isActive) return; // Prevent clicking when locked
        const itemHeight = 48;
        const index = parseInt(valStr, 10);
        container.scrollTo({ top: index * itemHeight, behavior: 'smooth' });
        // The scroll event listener already triggers `updateWheelStyle` automatically, 
        // but we can ensure it finishes cleanly:
        setTimeout(() => updateWheelStyle(container), 250); 
    }
    
    function getWheelValue(container) {
        const itemHeight = 48;
        const index = Math.round(container.scrollTop / itemHeight);
        return index.toString().padStart(2, '0');
    }
    
    function getSelectedTimes() {
        return {
            in: `${getWheelValue(inH)}:${getWheelValue(inM)}`,
            out: `${getWheelValue(outH)}:${getWheelValue(outM)}`
        };
    }

    // Initialize Default Times
    setTimeout(() => {
        setWheelValue(inH, "07");
        setWheelValue(inM, "30");
        setWheelValue(outH, "16");
        setWheelValue(outM, "00");
    }, 100);

    activateBtn.addEventListener('click', async () => {
      const newStatus = !isActive;
      const times = getSelectedTimes();
      
      const res = await fetch('/api/toggle', {
         method: 'POST',
         headers: {'Content-Type': 'application/json'},
         body: JSON.stringify({
            is_running: newStatus, 
            in_time: times.in, 
            out_time: times.out,
            selected_dates: selectedDates
         })
      });
      
      if(res.ok) {
          isActive = newStatus;
          updateUI(isActive);
      }
    });

    testBtn.addEventListener('click', async () => {
         await fetch('/api/test', {method: 'POST'});
    });
    
    function updateUI(active) {
      if (active) {
        activateBtn.innerText = 'Deactivate';
        activateBtn.classList.remove('bg-emerald-600', 'hover:bg-emerald-500', 'shadow-emerald-900/20');
        activateBtn.classList.add('bg-red-600/80', 'hover:bg-red-500/80', 'shadow-red-900/20');
        statusText.textContent = "System Active";
        statusText.classList.replace('text-slate-500', 'text-emerald-400');
        statusDot.classList.replace('bg-slate-500', 'bg-emerald-500');
        statusDot.classList.add('animate-pulse');
        
        // Lock Wheels & Dates
        wheelContainers.forEach(c => {
            c.style.overflowY = 'hidden';
            c.classList.add('opacity-50');
        });
        updateDateStyles();
      } else {
        activateBtn.innerText = 'Activate';
        activateBtn.classList.remove('bg-red-600/80', 'hover:bg-red-500/80', 'shadow-red-900/20');
        activateBtn.classList.add('bg-emerald-600', 'hover:bg-emerald-500', 'shadow-emerald-900/20');
        statusText.textContent = "System Standby";
        statusText.classList.replace('text-emerald-400', 'text-slate-500');
        statusDot.classList.replace('bg-emerald-500', 'bg-slate-500');
        statusDot.classList.remove('animate-pulse');
        countdownTimerText.textContent = "--:--:--";
        progressCircle.style.strokeDashoffset = 597;
        
        // Unlock Wheels & Dates
        wheelContainers.forEach(c => {
            c.style.overflowY = 'scroll';
            c.classList.remove('opacity-50');
        });
        updateDateStyles();
      }
    }
    
    // Polling status from server
    setInterval(async () => {
       try {
           const res = await fetch('/api/status');
           if(res.ok){
              const data = await res.json();
              if(data.is_running !== isActive) {
                 isActive = data.is_running;
                 if(data.selected_dates) {
                     selectedDates = data.selected_dates;
                 }
                 updateUI(isActive);
                 if(data.in_time && !isActive) {
                    const [h, m] = data.in_time.split(':');
                    setWheelValue(inH, h); setWheelValue(inM, m);
                 }
                 if(data.out_time && !isActive) {
                    const [h, m] = data.out_time.split(':');
                    setWheelValue(outH, h); setWheelValue(outM, m);
                 }
              }
              if(isActive && data.countdown !== "--:--:--") {
                 countdownTimerText.textContent = data.countdown;
                 
                 // Update circular progress line max 597 dashoffset
                 const seconds = data.total_seconds || 0;
                 const percentage = Math.max(0, Math.min(1, seconds / (12 * 3600)));
                 const offset = 597 - (597 * (1 - percentage));
                 progressCircle.style.strokeDashoffset = offset;
              }
           }
       } catch (e) { console.error(e); }
    }, 1000);
    
    // Attach exact scroll snap styling on load
    setTimeout(() => {
        wheelContainers.forEach(c => updateWheelStyle(c));
    }, 150);
    
    // Gracefully shut down python backend when the user closes the app window
    window.addEventListener('beforeunload', () => {
        navigator.sendBeacon('/api/shutdown');
    });
  </script>
<!-- END: Logic Handlers -->
</body></html>
"""

import socket
from flask import Flask, request, jsonify
from werkzeug.serving import make_server

app = Flask(__name__)

@app.route('/')
def index():
    return HTML_PAGE

@app.route('/api/status', methods=['GET'])
def get_status():
    countdown = "--:--:--"
    total_seconds = 0
    if state['is_running']:
        now = datetime.now()
        next_run = None
        
        selected_dates = sorted(state.get('selected_dates', []))
        for d_str in selected_dates:
            try:
                date_obj = datetime.strptime(d_str, '%Y-%m-%d')
                in_dt = date_obj.replace(hour=int(state['in_time'][:2]), minute=int(state['in_time'][3:]))
                out_dt = date_obj.replace(hour=int(state['out_time'][:2]), minute=int(state['out_time'][3:]))
                
                if in_dt > now and (next_run is None or in_dt < next_run):
                    next_run = in_dt
                if out_dt > now and (next_run is None or out_dt < next_run):
                    next_run = out_dt
            except:
                pass
                
        if next_run:
            diff = next_run - now
            total_seconds = int(diff.total_seconds())
            if total_seconds < 0: total_seconds = 0
            
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            countdown = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    return jsonify({
        "is_running": state['is_running'], 
        "countdown": countdown, 
        "total_seconds": total_seconds,
        "in_time": state['in_time'], 
        "out_time": state['out_time'],
        "selected_dates": state.get('selected_dates', [])
    })

@app.route('/api/toggle', methods=['POST'])
def toggle():
    data = request.get_json()
    state['is_running'] = data['is_running']
    state['in_time'] = data['in_time']
    state['out_time'] = data['out_time']
    state['selected_dates'] = data.get('selected_dates', [])
    
    schedule.clear()
    if state['is_running']:
        schedule.every().day.at(state['in_time']).do(perform_automation)
        schedule.every().day.at(state['out_time']).do(perform_automation)
        
    return jsonify({"status": "ok"})

@app.route('/api/test', methods=['POST'])
def test():
    threading.Thread(target=perform_automation, daemon=True).start()
    return jsonify({"status": "ok"})

@app.route('/api/shutdown', methods=['POST'])
def shutdown():
    print("UI Window Closed. Shutting down system entirely...")
    threading.Thread(target=lambda: (time.sleep(0.5), os._exit(0))).start()
    return jsonify({"status": "ok"})

import sys

# --- 1. SINGLE INSTANCE LOCK ---
# We bind a hidden socket to a specific port to prove we are the only running worker. 
# If a user double-clicks the app multiple times, ghost instances will fail to bind and instantly exit safely.
lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    lock_socket.bind(('127.0.0.1', 54321))
except socket.error:
    print("Application is already actively running in the background. Exiting.")
    sys.exit(0)

if __name__ == "__main__":
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR) # Silence verbose Flask logs
    
    # We flip the architecture: 
    # Let Flask own the main thread completely so it never blocks.
    # The Scheduler loop goes into background.
    def run_scheduler_bg():
        print("Scheduler running in background...")
        while True:
            if state['is_running']:
                schedule.run_pending()
            time.sleep(1)
            
    sch_thread = threading.Thread(target=run_scheduler_bg, daemon=True)
    sch_thread.start()
    
    # Pre-bind the port securely before Flask starts so we know exactly where it goes.
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0)) # OS assigns free port
    assigned_port = s.getsockname()[1]
    s.close() # Free it for flask
    
    url = f"http://127.0.0.1:{assigned_port}"
    print(f"\n==============================================")
    print(f"Server is exclusively running on: {url}")
    print(f"==============================================\n")
    
    import subprocess
    
    # Schedule the browser to open only exactly after flask starts absorbing connections
    def safe_browser_open():
        time.sleep(1.5)
        edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        try:
            if os.path.exists(edge_path):
                print("Launching native Edge App Mode...")
                subprocess.Popen([edge_path, f"--app={url}"])
            else:
                webbrowser.open_new(url)
            print("UI successfully launched in browser.")
        except Exception as e:
            print(f"Please open your browser manually to: {url}")
            
    threading.Thread(target=safe_browser_open, daemon=True).start()
    
    print("Press Ctrl+C or Close the UI Window to Exit the application entirely.")
    
    try:
        # Flask securely binds to the main OS thread to perfectly serve requests 100% reliably
        app.run(host="127.0.0.1", port=assigned_port, threaded=True, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        pass

