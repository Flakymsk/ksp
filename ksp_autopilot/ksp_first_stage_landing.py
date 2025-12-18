import krpc
import time
import matplotlib.pyplot as plt

conn = krpc.connect(
    name='KSP Autopilot',
    address='127.0.0.1',
    rpc_port=50000, stream_port=50001)
print('Server connected!')

vessel = conn.space_center.active_vessel
flight_info = vessel.flight(vessel.orbit.body.reference_frame)

time_stream = conn.add_stream(getattr, vessel, 'met')
altitude_stream = conn.add_stream(getattr, flight_info, 'mean_altitude')
speed_stream = conn.add_stream(getattr, flight_info, 'speed')

times = []
altitudes = []
speeds = []

plt.ion()
fig1, ax1 = plt.subplots(figsize=(10, 5))
fig2, ax2 = plt.subplots(figsize=(10, 5))

line_alt, = ax1.plot([], [], 'b-', linewidth=2)
ax1.set_title('Высота первой ступени')
ax1.set_xlabel('Время (с)')
ax1.set_ylabel('Высота (м)')
ax1.grid(True)

line_speed, = ax2.plot([], [], 'g-', linewidth=2)
ax2.set_title('Скорость первой ступени')
ax2.set_xlabel('Время (с)')
ax2.set_ylabel('Скорость (м/с)')
ax2.grid(True)


def update_graphs():
    if times:
        line_alt.set_data(times, altitudes)
        ax1.relim()
        ax1.autoscale_view()
        fig1.canvas.draw()
        fig1.canvas.flush_events()

        line_speed.set_data(times, speeds)
        ax2.relim()
        ax2.autoscale_view()
        fig2.canvas.draw()
        fig2.canvas.flush_events()


vessel.control.sas = True
time.sleep(1)
vessel.control.sas_mode = conn.space_center.SASMode.retrograde
time.sleep(5)

while altitude_stream() > 10000:
    times.append(time_stream())  # ← используем time_stream() вместо time.time()
    altitudes.append(altitude_stream())
    speeds.append(speed_stream())
    update_graphs()
    time.sleep(0.5)

while not vessel.situation == conn.space_center.VesselSituation.landed:
    times.append(time_stream())
    altitudes.append(altitude_stream())
    speeds.append(speed_stream())
    update_graphs()
    time.sleep(0.1)

time_stream.remove()
altitude_stream.remove()
speed_stream.remove()

plt.ioff()
plt.show()
