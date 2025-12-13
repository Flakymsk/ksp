import krpc
import time
import numpy as np
import matplotlib.pyplot as plt


conn = krpc.connect(
    name='KPS Autopilot',
    address='127.0.0.1',
    rpc_port=50000, stream_port=50001)
print('Server connected!')

vessel = conn.space_center.active_vessel
print(vessel.name)

vessel.control.sas = True
vessel.control.sas_mode = vessel.control.sas_mode.stability_assist
vessel.control.throttle = 1
time.sleep(1)

vessel_height_stream = conn.add_stream(getattr, vessel.flight(), 'mean_altitude')

print('Launch!')
vessel.control.activate_next_stage()
vessel_time_since_start_stream = conn.add_stream(getattr, vessel, 'met')


first_stage_fuel_amount_stream = conn.add_stream(vessel.resources_in_decouple_stage(3).amount, 'LiquidFuel')


def append_array_height_time(arr, height, time):
    arr.append(arr[0], height, 1)
    arr.append(arr[1], time, 1)

def vessel_to_orbite(heading_start, heading_end, seconds_wait):

    for i in range(heading_start - heading_end + 1):
        vessel.auto_pilot.target_pitch_and_heading(heading_start- i, 90)
        event = conn.krpc.add_event(
            conn.krpc.Expression.greater_than(
                conn.krpc.Expression.call(
                    conn.get_call(getattr, conn.space_center, 'ut')
                ),
                conn.krpc.Expression.constant_double(
                    conn.space_center.ut + seconds_wait
                )
            )
        )
        with event.condition:
            event.wait()

    event.remove()


plt.ion()
plt.title('График старта ракеты')
plt.xlabel('Время, с')
plt.ylabel('Высота, м')
plt.grid(True)
plt.xlim(0, 300)
plt.ylim(0, 30000)
plt.show()


array_height_time = np.array([vessel_height_stream()],[vessel_time_since_start_stream()])

while vessel_height_stream() < 28500.0:

    if vessel_height_stream() > 500.0 and vessel_height_stream() < 2000.0:
        print(f"Высота: {vessel_height_stream():.1f} м, Топливо: {first_stage_fuel_amount_stream():.2f}")
        append_array_height_time(array_height_time, vessel_height_stream,vessel_time_since_start_stream)

        vessel.auto_pilot.engage()
        vessel_to_orbite(90, 85, 5)

    elif vessel_height_stream() > 2000.0 and vessel_height_stream() < 5000.0:
        print(f"Высота: {vessel_height_stream():.1f} м, Топливо: {first_stage_fuel_amount_stream():.2f}")
        append_array_height_time(array_height_time, vessel_height_stream,vessel_time_since_start_stream)

        vessel_to_orbite(85,75,3)

    elif vessel_height_stream() > 5000.0 and vessel_height_stream() < 10000.0:
        print(f"Высота: {vessel_height_stream():.1f} м, Топливо: {first_stage_fuel_amount_stream():.2f}")
        append_array_height_time(array_height_time, vessel_height_stream,vessel_time_since_start_stream)

        vessel_to_orbite(75, 60, 3)

    elif vessel_height_stream() > 10000.0 and vessel_height_stream() < 15000.0:
        print(f"Высота: {vessel_height_stream():.1f} м, Топливо: {first_stage_fuel_amount_stream():.2f}")
        append_array_height_time(array_height_time, vessel_height_stream,vessel_time_since_start_stream)

        vessel_to_orbite(60, 45, 3.2)

    elif vessel_height_stream() > 15000.0 and vessel_height_stream() < 20000.0:
        print(f"Высота: {vessel_height_stream():.1f} м, Топливо: {first_stage_fuel_amount_stream():.2f}")
        append_array_height_time(array_height_time, vessel_height_stream,vessel_time_since_start_stream)

        vessel_to_orbite(45, 40, 10)

    elif vessel_height_stream() > 20000.0 and vessel_height_stream() < 25000.0:
        print(f"Высота: {vessel_height_stream():.1f} м, Топливо: {first_stage_fuel_amount_stream():.2f}")
        append_array_height_time(array_height_time, vessel_height_stream,vessel_time_since_start_stream)

        vessel_to_orbite(40, 35, 11)
    elif vessel_height_stream() > 25000.0:
        print(f"Высота: {vessel_height_stream():.1f} м, Топливо: {first_stage_fuel_amount_stream():.2f}")
        append_array_height_time(array_height_time, vessel_height_stream,vessel_time_since_start_stream)

        vessel_to_orbite(35, 30, 12)

    time.sleep(0.5)

print('Активация следующей ступени')
vessel.control.activate_next_stage()


vessel_height_stream.remove()
first_stage_fuel_amount_stream.remove()
vessel_time_since_start_stream.remove()