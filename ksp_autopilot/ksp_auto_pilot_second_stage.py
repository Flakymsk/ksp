import krpc
import time
import matplotlib.pyplot as plt

conn = krpc.connect(
    name='KSP Autopilot',
    address='127.0.0.1',
    rpc_port=50000, stream_port=50001)
print('Server connected!')

vessel = conn.space_center.active_vessel

vessel.control.sas = True
vessel.control.throttle = 1
time.sleep(1)

print(vessel.name)
vessel_height_stream = conn.add_stream(getattr, vessel.flight(), 'mean_altitude')
vessel_time_since_start_stream = conn.add_stream(getattr, vessel, 'met')

vessel_speed_stream = conn.add_stream(getattr, vessel.flight(vessel.orbit.body.reference_frame), 'speed')

vessel_apoapsis_stream = conn.add_stream(getattr, vessel.orbit, 'apoapsis_altitude')
vessel_periapsis_stream = conn.add_stream(getattr, vessel.orbit, 'periapsis_altitude')


times = []
heights = []
apoapsis = []
periapsis = []
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

fig3, ax3 = plt.subplots(figsize=(10, 5))
line_apoapsis, = ax3.plot([], [], 'g-', linewidth=2)
ax3.set_title('Высота апогея')
ax3.set_xlabel('Время (с)')
ax3.set_ylabel('Высота (м)')
ax3.grid(True)

fig4, ax4 = plt.subplots(figsize=(10, 5))
line_periapsis, = ax4.plot([], [], 'g-', linewidth=2)
ax4.set_title('Высота перигея')
ax4.set_xlabel('Время (с)')
ax4.set_ylabel('Высота (м)')
ax4.grid(True)

def update_graph_height():
    if times:
        line_height.set_data(times, heights)
        ax1.relim()
        ax1.autoscale_view()
        fig1.canvas.draw()
        fig1.canvas.flush_events()


def update_graph_height_apoapsis():
    if times:
        line_apoapsis.set_data(times, apoapsis)
        ax3.relim()
        ax3.autoscale_view()
        fig3.canvas.draw()
        fig3.canvas.flush_events()


def update_graph_height_periapsis():
    if times and periapsis:
        available_times = times[:len(periapsis)]
        line_periapsis.set_data(available_times, periapsis)
        ax4.relim()
        ax4.autoscale_view()
        fig4.canvas.draw()
        fig4.canvas.flush_events()


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

print('Launch!')
vessel.control.activate_next_stage()
first_stage_fuel_amount = vessel.resources_in_decouple_stage(2).amount
first_stage_fuel_amount_stream = conn.add_stream(first_stage_fuel_amount, 'LiquidFuel')

while vessel_height_stream() < 27500.0:
    times.append(vessel_time_since_start_stream())
    heights.append(vessel_height_stream())
    apoapsis.append(vessel_apoapsis_stream())
    speeds.append(vessel_speed_stream())

    update_graph_height()
    update_graph_speed()
    update_graph_height_apoapsis()

    if 6000.0 < vessel_height_stream() < 11000.0:
        print(f"Высота: {vessel_height_stream():.1f} м, Топливо: {first_stage_fuel_amount_stream() * 5:.2f} тонн.")
        vessel.auto_pilot.engage()
        vessel.auto_pilot.attenuation_angle = (2.0, 2.0, 2.0)
        vessel.auto_pilot.stopping_time = (0.8, 0.8, 0.8)
        vessel_to_orbite(90, 75, 1.3)

    elif 11000.0 < vessel_height_stream() < 16000.0:
        print(f"Высота: {vessel_height_stream():.1f} м, Топливо: {first_stage_fuel_amount_stream() * 5:.2f} тонн.")
        vessel_to_orbite(75, 65, 1.5)

    elif 16000.0 < vessel_height_stream() < 20000.0:
        print(f"Высота: {vessel_height_stream():.1f} м, Топливо: {first_stage_fuel_amount_stream() * 5:.2f} тонн.")
        vessel_to_orbite(65, 60, 1)

    elif 20000.0 < vessel_height_stream() < 25000.0:
        print(f"Высота: {vessel_height_stream():.1f} м, Топливо: {first_stage_fuel_amount_stream() * 5:.2f} тонн.")
        vessel_to_orbite(60, 50, 0.7)

    elif vessel_height_stream() > 25000.0:
        print(f"Высота: {vessel_height_stream():.1f} м, Топливо: {first_stage_fuel_amount_stream() * 5:.2f} тонн.")
        vessel_to_orbite(50, 45, 0.3)

    time.sleep(0.05)

first_stage_fuel_amount_stream.remove()
vessel_speed_stream.remove()
vessel_speed_stream = conn.add_stream(getattr, vessel.flight(vessel.orbit.body.non_rotating_reference_frame), 'speed')

print('Активация следующей ступени.')
vessel.control.throttle = 0
time.sleep(1)
vessel.control.activate_next_stage()
vessel.auto_pilot.target_pitch_and_heading(45, 90)
vessel.control.throttle = 1

while vessel_apoapsis_stream() < 80000.0:

    times.append(vessel_time_since_start_stream())
    heights.append(vessel_height_stream())
    apoapsis.append(vessel_apoapsis_stream())
    speeds.append(vessel_speed_stream())

    update_graph_height()
    update_graph_height_apoapsis()
    update_graph_speed()

    time.sleep(0.05)

print('Вторая ступень набрала скорость для выхода на 80 км, ожидаем выхода на апогей.')
vessel.control.throttle = 0


while vessel_height_stream() < 78000.0:
    times.append(vessel_time_since_start_stream())
    heights.append(vessel_height_stream())
    apoapsis.append(vessel_apoapsis_stream())
    speeds.append(vessel_speed_stream())

    update_graph_height()
    update_graph_height_apoapsis()
    update_graph_speed()

    time.sleep(0.01)

vessel.control.rcs = True
vessel.auto_pilot.disengage()
vessel.control.sas = True
time.sleep(1)
vessel.control.sas_mode = conn.space_center.SASMode.prograde
time.sleep(1)

print('Вторая ступень почти достигла апогея, включаем двигатели.')

vessel.control.throttle = 1

while vessel_periapsis_stream() < 79900.0:

    times.append(vessel_time_since_start_stream())
    heights.append(vessel_height_stream())
    apoapsis.append(vessel_apoapsis_stream())
    periapsis.append(vessel_periapsis_stream())
    speeds.append(vessel_speed_stream())

    update_graph_height()
    update_graph_height_apoapsis()
    update_graph_height_periapsis()
    update_graph_speed()

    time.sleep(0.05)

vessel.control.throttle = 0
print('Вторая ступень набрала скорость для высоты перигея 80 км, выключаем двигатели.')

while vessel_height_stream() > 35000.0:
    times.append(vessel_time_since_start_stream())
    heights.append(vessel_height_stream())
    apoapsis.append(vessel_apoapsis_stream())
    periapsis.append(vessel_periapsis_stream())
    speeds.append(vessel_speed_stream())

    update_graph_height()
    update_graph_height_apoapsis()
    update_graph_height_periapsis()
    update_graph_speed()

    time.sleep(1.0)

vessel_speed_stream.remove()
vessel_speed_stream = conn.add_stream(getattr, vessel.flight(vessel.orbit.body.reference_frame), 'speed')

while not vessel.situation == conn.space_center.VesselSituation.landed:
    times.append(vessel_time_since_start_stream())
    heights.append(vessel_height_stream())
    speeds.append(vessel_speed_stream())

    update_graph_height()
    update_graph_speed()

    time.sleep(0.1)

plt.ioff()
plt.show()

vessel_height_stream.remove()
vessel_speed_stream.remove()
vessel_apoapsis_stream.remove()
vessel_periapsis_stream.remove()
vessel_time_since_start_stream.remove()