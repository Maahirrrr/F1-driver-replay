"""
F1 Driver Tracker - Live Animation System
Real-time visualization of F1 driver positions on track using FastF1 telemetry

Requirements:
pip install fastf1 matplotlib numpy pandas
"""

import fastf1 as ff1 
from fastf1 import plotting 
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button, Slider
import os 
import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)

# =========================================================
# 1. SETUP & CONFIGURATION (Optimized FPS)
# =========================================================
cache_dir = 'cache'
if not os.path.exists(cache_dir):
    print(f"Creating cache directory: {cache_dir}")
    os.makedirs(cache_dir)

ff1.Cache.enable_cache(cache_dir) 

# --- SESSION PARAMETERS ---
YEAR = 2023
RACE = 'Monaco'
SESSION = 'Q'  
NUM_DRIVERS = 10 

# OPTIMIZATION: Set FPS higher for powerful machines
FPS = 90

# Global state variables for controlling the animation
all_interpolated_data = []
current_drivers_data = []
current_frame = 0
all_lap_telemetry = {} 
total_seconds = 0
times = np.array([])
is_paused = False
slider_active = False  # Track if slider is being manually controlled

# =========================================================
# 2. DATA LOADING & SYNCHRONIZATION
# =========================================================

def load_and_synchronize_data():
    """Loads session data, filters fastest laps, and interpolates data."""
    global all_interpolated_data, all_lap_telemetry, total_seconds, times
    
    print(f"\nLoading {YEAR} {RACE} - {SESSION}...")
    session = ff1.get_session(YEAR, RACE, SESSION)
    session.load(telemetry=True, weather=False, laps=True) 

    # 2a. Prepare data for All-Grid Tracking (Top N Fastest Laps)
    laps = session.laps
    laps = laps[laps['LapTime'].notna()].reset_index(drop=True)
    
    if len(laps) == 0:
        raise ValueError("No valid laps found in session data.")
    
    fastest_laps = laps.loc[laps.groupby('Driver')['LapTime'].idxmin()].sort_values(by='LapTime')
    drivers_to_track = fastest_laps.head(NUM_DRIVERS)
    
    max_time_list = []
    temp_raw_telemetry_list = []
    
    print(f"Preparing data for the Top {NUM_DRIVERS} drivers...")

    # 2b. Interpolation Function
    def interpolate_telemetry(telemetry, time_index):
        tel_seconds = telemetry['Time'].dt.total_seconds().to_numpy()
        x_interp = np.interp(time_index, tel_seconds, telemetry['X'])
        y_interp = np.interp(time_index, tel_seconds, telemetry['Y'])
        speed_interp = np.interp(time_index, tel_seconds, telemetry['Speed'])
        return x_interp, y_interp, speed_interp

    # Pre-fetch raw telemetry for max_time calculation
    for index, row in drivers_to_track.iterrows():
        try:
            tel = row.get_telemetry()
            if tel is not None and not tel.empty:
                max_time_list.append(tel['Time'].max())
                temp_raw_telemetry_list.append((row, tel))
        except Exception as e:
            print(f"Skipping {row['Driver']} - No telemetry available")
            continue
    
    if not max_time_list:
        raise ValueError("No valid telemetry data found for the top drivers.")

    # Calculate common timeline
    total_seconds = max(max_time_list).total_seconds()
    times = np.arange(0, total_seconds, 1/FPS)

    # 2c. Interpolate and store all data
    for row, tel in temp_raw_telemetry_list:
        driver = row['Driver']
        
        x_interp, y_interp, speed_interp = interpolate_telemetry(tel, times)
        
        try:
            color = plotting.get_driver_color(driver, session=session)
        except:
            try:
                color = plotting.get_team_color(row['Team'], session=session)
            except:
                color = '#FFFFFF'
        
        # PRE-CALCULATE cumulative distances for performance
        cumulative_distances = np.zeros(len(x_interp))
        for i in range(1, len(x_interp)):
            dx = x_interp[i] - x_interp[i-1]
            dy = y_interp[i] - y_interp[i-1]
            cumulative_distances[i] = cumulative_distances[i-1] + np.sqrt(dx**2 + dy**2)
        
        data = {
            'Driver': driver,
            'Color': color,
            'X_interp': x_interp,
            'Y_interp': y_interp,
            'Speed_interp': speed_interp,
            'LapTime': row['LapTime'],
            'CumulativeDistance': cumulative_distances  # Store pre-calculated distances
        }
        all_interpolated_data.append(data)
        
        # Store single lap data for the dropdown menu selection
        all_lap_telemetry[f"{driver} - Lap {row['LapNumber']}"] = data
    
    if len(all_interpolated_data) == 0:
        raise ValueError("No driver data was successfully loaded.")
            
    # Set initial state to All-Grid view
    global current_drivers_data
    current_drivers_data = all_interpolated_data.copy()

# Run data loading before setting up the plot
try:
    load_and_synchronize_data()
except ValueError as e:
    print(f"Error during data loading: {e}")
    exit()

# =========================================================
# 3. ANIMATION & PLOTTING SETUP
# =========================================================

plotting.setup_mpl() 
plt.style.use('dark_background')

# Create the main figure and the track map axes
fig = plt.figure(figsize=(14, 10))

# Main Track Map Axes (occupies most of the figure)
ax_map = fig.add_axes([0.05, 0.15, 0.7, 0.75])
ax_map.set_aspect('equal')
ax_map.axis('off')

# Control Panel Axes
ax_controls = fig.add_axes([0.78, 0.15, 0.2, 0.75], facecolor='black')
ax_controls.axis('off')

# Plot the static track map (using the first driver's path)
track_outline = ax_map.plot(
    all_interpolated_data[0]['X_interp'], 
    all_interpolated_data[0]['Y_interp'], 
    color='white', linewidth=2, alpha=0.3, zorder=1
)[0]

# Initialize all the "Ghost" dots (actual plot objects)
dots = []
dot_labels = []
for data in current_drivers_data:
    dot, = ax_map.plot([], [], marker='o', color=data['Color'], markersize=14, 
                      label=data['Driver'], zorder=10, markeredgecolor='white', markeredgewidth=1.5)
    dots.append(dot)
    
    # Add driver label next to dot
    label = ax_map.text(0, 0, '', color='white', fontsize=9, weight='bold',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.7))
    dot_labels.append(label)

# Dynamic text elements
time_text = ax_map.text(0.05, 0.98, '', transform=ax_map.transAxes, 
                       color='white', fontsize=14, weight='bold',
                       bbox=dict(boxstyle='round', facecolor='black', alpha=0.7))

speed_text = ax_map.text(0.05, 0.93, '', transform=ax_map.transAxes, 
                        color='cyan', fontsize=12, weight='bold',
                        bbox=dict(boxstyle='round', facecolor='black', alpha=0.7))

# Gap display for ghost mode (initially hidden)
gap_text = ax_map.text(0.05, 0.88, '', transform=ax_map.transAxes, 
                      color='yellow', fontsize=13, weight='bold',
                      bbox=dict(boxstyle='round', facecolor='black', alpha=0.7))
gap_text.set_visible(False)

title_text = fig.suptitle(f"{RACE} {YEAR} - Driver Tracker (Full Grid)", 
                          color='white', fontsize=18, weight='bold')

# Legend
legend = ax_map.legend([dot for dot in dots], [data['Driver'] for data in current_drivers_data], 
                      loc='lower right', facecolor='black', edgecolor='white', 
                      labelcolor='white', fontsize=9)

# =========================================================
# 4. WIDGET DEFINITIONS AND CALLBACKS
# =========================================================

def reset_plot_objects():
    """Resets the dots and updates the legend based on current_drivers_data."""
    global dots, dot_labels, legend
    
    # Clear existing dots and labels
    for dot in dots:
        dot.remove()
    for label in dot_labels:
        label.remove()
    dots = []
    dot_labels = []
    
    # Re-initialize new dots based on the current data
    for data in current_drivers_data:
        dot, = ax_map.plot([], [], marker='o', color=data['Color'], markersize=14, 
                          label=data['Driver'], zorder=10, markeredgecolor='white', markeredgewidth=1.5)
        dots.append(dot)
        
        label = ax_map.text(0, 0, '', color='white', fontsize=9, weight='bold',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.7))
        dot_labels.append(label)
    
    # Recreate the legend
    if legend:
        legend.remove()
    legend = ax_map.legend([dot for dot in dots], [data['Driver'] for data in current_drivers_data], 
                          loc='lower right', facecolor='black', edgecolor='white', 
                          labelcolor='white', fontsize=9)
    
    # Restart the animation frame count
    global current_frame
    current_frame = 0
    fig.canvas.draw_idle()


# --- Ghost Mode Switch Button ---
ax_button = fig.add_axes([0.8, 0.85, 0.15, 0.04])
ghost_button = Button(ax_button, 'Ghost Mode (Top 2)', color='#444444', hovercolor='#666666')
ghost_button.label.set_color('white')
ghost_button.label.set_weight('bold')
ghost_mode_on = False

def ghost_mode_callback(event):
    """Switches between All-Grid and Top 2 views."""
    global current_drivers_data, ghost_mode_on
    
    ghost_mode_on = not ghost_mode_on
    
    if ghost_mode_on:
        if len(all_interpolated_data) >= 2:
            current_drivers_data = all_interpolated_data[:2]
            ghost_button.label.set_text('Full Grid Mode')
            title_text.set_text(f"{RACE} {YEAR} - Ghost Mode (Top 2)")
            gap_text.set_visible(True)
        else:
            print("Not enough drivers for ghost mode")
            ghost_mode_on = False
            return
    else:
        current_drivers_data = all_interpolated_data.copy()
        ghost_button.label.set_text('Ghost Mode (Top 2)')
        title_text.set_text(f"{RACE} {YEAR} - Driver Tracker (Full Grid)")
        gap_text.set_visible(False)
    
    reset_plot_objects()

ghost_button.on_clicked(ghost_mode_callback)


# --- Play/Pause Button ---
ax_pause_button = fig.add_axes([0.8, 0.78, 0.15, 0.04])
pause_button = Button(ax_pause_button, 'Pause', color='#444444', hovercolor='#666666')
pause_button.label.set_color('white')
pause_button.label.set_weight('bold')

def pause_callback(event):
    """Toggles animation pause."""
    global is_paused
    is_paused = not is_paused
    pause_button.label.set_text('Play' if is_paused else 'Pause')

pause_button.on_clicked(pause_callback)


# --- Reset Button ---
ax_reset_button = fig.add_axes([0.8, 0.71, 0.15, 0.04])
reset_button = Button(ax_reset_button, 'Reset', color='#444444', hovercolor='#666666')
reset_button.label.set_color('white')
reset_button.label.set_weight('bold')

def reset_callback(event):
    """Resets animation to start."""
    global current_frame, slider_active
    current_frame = 0
    slider_active = False
    progress_slider.set_val(0)

reset_button.on_clicked(reset_callback)


# --- Progress Slider ---
ax_slider = fig.add_axes([0.1, 0.05, 0.6, 0.03])
progress_slider = Slider(ax_slider, 'Track Completion', 0, 100, valinit=0, 
                        valstep=0.1, color='red', valfmt='%0.1f%%')

def slider_update(val):
    """Update animation frame based on slider."""
    global current_frame, slider_active
    slider_active = True
    # Convert percentage to frame number
    current_frame = int((val / 100) * (len(times) - 1))
    current_frame = max(0, min(current_frame, len(times) - 1))  # Bounds checking

progress_slider.on_changed(slider_update)


# Display lap times
lap_times_text = "Lap Times:\n" + "━"*20 + "\n"
for i, data in enumerate(all_interpolated_data[:5]):
    lap_time = str(data['LapTime'])[10:18]
    lap_times_text += f"{i+1}. {data['Driver']}: {lap_time}\n"

ax_controls.text(0.05, 0.4, lap_times_text, transform=ax_controls.transAxes,
                fontsize=8, color='cyan', verticalalignment='top',
                family='monospace')

# =========================================================
# 5. RUN ANIMATION
# =========================================================

def update(frame):
    """Update function called for each frame of the animation."""
    global current_frame, slider_active
    
    if is_paused:
        return tuple(dots + dot_labels + [time_text, speed_text, gap_text])
    
    # Only update current_frame from animation if slider is not being manually controlled
    if not slider_active:
        current_frame = frame % len(times)
    else:
        # Reset slider_active after one frame to resume normal animation
        slider_active = False
    
    # Ensure current_frame is within valid bounds
    current_frame = max(0, min(current_frame, len(times) - 1))
    
    # Update slider to show percentage (without triggering callback)
    progress_percentage = (current_frame / (len(times) - 1)) * 100 if len(times) > 1 else 0
    progress_slider.eventson = False  # Disable events temporarily
    progress_slider.set_val(progress_percentage)
    progress_slider.eventson = True  # Re-enable events
    
    return_objects = []
    max_speed = 0
    
    # Track cumulative distances for gap calculation (now using pre-calculated values)
    driver_cumulative_distances = []
    
    # Update each driver's position
    for idx, (dot, label, data) in enumerate(zip(dots, dot_labels, current_drivers_data)):
        
        if current_frame < len(data['X_interp']):
            x_pos = data['X_interp'][current_frame]
            y_pos = data['Y_interp'][current_frame]
            speed = data['Speed_interp'][current_frame]
            
            dot.set_data([x_pos], [y_pos])
            label.set_position((x_pos + 50, y_pos + 50))
            label.set_text(data['Driver'])
            
            max_speed = max(max_speed, speed)
            
            # Use pre-calculated cumulative distance (MUCH faster!)
            cumulative_dist = data['CumulativeDistance'][current_frame]
            driver_cumulative_distances.append(cumulative_dist)
        else:
            driver_cumulative_distances.append(0)
        
        return_objects.extend([dot, label])
    
    # Update time display
    current_time = times[current_frame] if current_frame < len(times) else 0
    time_text.set_text(f"Time: {current_time:.2f}s")
    speed_text.set_text(f"Max Speed: {max_speed:.0f} km/h")
    
    # Calculate and display LIVE gap in ghost mode
    if ghost_mode_on and len(current_drivers_data) == 2 and len(driver_cumulative_distances) == 2:
        driver1_name = current_drivers_data[0]['Driver']
        driver2_name = current_drivers_data[1]['Driver']
        
        # Distance difference between the two drivers
        distance_gap = driver_cumulative_distances[0] - driver_cumulative_distances[1]
        
        # Convert distance to approximate time gap using current speed
        # Use a weighted average of both drivers' speeds for more accuracy
        if current_frame < len(current_drivers_data[0]['Speed_interp']) and \
           current_frame < len(current_drivers_data[1]['Speed_interp']):
            speed1 = current_drivers_data[0]['Speed_interp'][current_frame]
            speed2 = current_drivers_data[1]['Speed_interp'][current_frame]
            avg_speed_kmh = (speed1 + speed2) / 2
            avg_speed_mps = avg_speed_kmh / 3.6 if avg_speed_kmh > 0 else 1
        else:
            avg_speed_mps = max_speed / 3.6 if max_speed > 0 else 1
        
        time_gap = abs(distance_gap) / avg_speed_mps if avg_speed_mps > 0 else 0
        
        # Display based on who is ahead
        if abs(distance_gap) < 1:  # Less than 1 meter difference
            gap_text.set_text(f"Gap: Side by side")
        elif distance_gap > 0:
            gap_text.set_text(f"Gap: {driver1_name} ahead by {time_gap:.3f}s")
        else:
            gap_text.set_text(f"Gap: {driver2_name} ahead by {time_gap:.3f}s")
    
    return_objects.extend([time_text, speed_text, gap_text])
    
    return tuple(return_objects)

# Create the animation object
ani = FuncAnimation(
    fig, 
    update, 
    frames=len(times), 
    interval=1000/FPS,
    blit=False,
    repeat=True
)

print(f"\n✅ Animation ready! Running at {FPS} FPS.")
print(f"📊 Tracking {len(current_drivers_data)} drivers")
print(f"⏱ Total duration: {total_seconds:.2f} seconds")
print(f"🏁 Race: {YEAR} {RACE} - {SESSION}")
print("\n🎮 Use the controls to interact with the animation!")
print("━" * 50)

plt.show()