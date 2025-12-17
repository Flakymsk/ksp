import krpc
import time
import matplotlib.pyplot as plt

conn = krpc.connect(
    name='KSP Autopilot',
    address='127.0.0.1',
    rpc_port=50000, stream_port=50001)
print('Server connected!')

vessel = conn.space_center.active_vessel
print(vessel.name)

vessel.control.sas = True
vessel.control.throttle = 1
time.sleep(1)

vessel_height_stream = conn.add_stream(getattr, vessel.flight(), 'mean_altitude')
vessel_time_since_start_stream = conn.add_stream(getattr, vessel, 'met')
flight_info = vessel.flight(vessel.surface_reference_frame)
vessel_speed_stream = conn.add_stream(getattr, vessel.flight(vessel.orbit.body.reference_frame), 'speed')
vessel_apoapsis_stream = conn.add_stream(getattr, vessel.orbit, 'apoapsis_altitude')

print('Launch!')
vessel.control.activate_next_stage()
first_stage_fuel_amount = vessel.resources_in_decouple_stage(2).amount
first_stage_fuel_amount_stream = conn.add_stream(first_stage_fuel_amount, 'LiquidFuel')

times = []
heights = []
speeds = []

plt.ion()
fig1, ax1 = plt.subplots(figsize=(10, 5))
line_height, = ax1.plot([], [], 'b-', linewidth=2)
ax1.set_title('Высота ракеты')
ax1.set_xlabel('Время (с)')
ax1.set_ylabel('Высота (м)')
ax1.grid(True)

fig2, ax2 = plt.subplots(figsize=(10, 5))
line_speed, = ax2.plot([], [], 'g-', linewidth=2)
ax2.set_title('Скорость ракеты')
ax2.set_xlabel('Время (с)')
ax2.set_ylabel('Скорость (м/с)')
ax2.grid(True)



def update_graph_height():
    if times:
        line_height.set_data(times, heights)
        ax1.relim()
        ax1.autoscale_view()
        fig1.canvas.draw()
        fig1.canvas.flush_events()


def update_graph_speed():
    if times:
        line_speed.set_data(times, speeds)
        ax2.relim()
        ax2.autoscale_view()
        fig2.canvas.draw()
        fig2.canvas.flush_events()


def vessel_to_orbite(heading_start, heading_end, seconds_wait):
    for i in range(heading_start - heading_end + 1):
        vessel.auto_pilot.target_pitch_and_heading(heading_start - i, 90)
        time.sleep(seconds_wait)


while vessel_height_stream() < 27500.0:

    times.append(vessel_time_since_start_stream())
    heights.append(vessel_height_stream())
    speeds.append(vessel_speed_stream())

    update_graph_height()
    update_graph_speed()

    if 5000.0 < vessel_height_stream() < 10000.0:
        print(f"Высота: {vessel_height_stream():.1f} м, Топливо: {first_stage_fuel_amount_stream() * 5:.2f} тонн.")
        vessel.auto_pilot.engage()
        vessel.auto_pilot.attenuation_angle = (2.0, 2.0, 2.0)
        vessel.auto_pilot.stopping_time = (0.8, 0.8, 0.8)
        vessel_to_orbite(90, 75, 1.3)

    elif 10000.0 < vessel_height_stream() < 15000.0:
        print(f"Высота: {vessel_height_stream():.1f} м, Топливо: {first_stage_fuel_amount_stream() * 5:.2f} тонн.")
        vessel_to_orbite(75, 65, 1.5)

    elif 15000.0 < vessel_height_stream() < 20000.0:
        print(f"Высота: {vessel_height_stream():.1f} м, Топливо: {first_stage_fuel_amount_stream() * 5:.2f} тонн.")
        vessel_to_orbite(65, 60, 1)

    elif 20000.0 < vessel_height_stream() < 25000.0:
        print(f"Высота: {vessel_height_stream():.1f} м, Топливо: {first_stage_fuel_amount_stream() * 5:.2f} тонн.")
        vessel_to_orbite(60, 50, 0.7)

    elif vessel_height_stream() > 25000.0:
        print(f"Высота: {vessel_height_stream():.1f} м, Топливо: {first_stage_fuel_amount_stream() * 5:.2f} тонн.")
        vessel_to_orbite(50, 45, 0.3)

    time.sleep(0.05)

print('Активация следующей ступени')
vessel.control.throttle = 0
time.sleep(1)
vessel.control.activate_next_stage()

vessel.control.throttle = 1
vessel.auto_pilot.target_pitch_and_heading(90,90)

while vessel_height_stream() < 70000.0:
    times.append(vessel_time_since_start_stream())
    heights.append(vessel_height_stream())
    speeds.append(vessel_speed_stream())

    update_graph_height()
    update_graph_speed()

    time.sleep(0.05)

print("Вторая ступень вышла из атмосферы, теперь можно переключиться на первую")
vessel.control.throttle = 0

while vessel_height_stream() > 0.0:
    times.append(vessel_time_since_start_stream())
    heights.append(vessel_height_stream())
    speeds.append(vessel_speed_stream())

    update_graph_height()
    update_graph_speed()

    time.sleep(1.0)

plt.ioff()
plt.show()

vessel_height_stream.remove()
vessel_speed_stream.remove()
vessel_apoapsis_stream.remove()
first_stage_fuel_amount_stream.remove()
vessel_time_since_start_stream.remove()