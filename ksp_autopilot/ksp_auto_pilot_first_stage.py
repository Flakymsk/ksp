import krpc
import time

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
flight_info = vessel.flight(vessel.surface_reference_frame)
vessel_speed_stream = conn.add_stream(getattr, vessel.flight(vessel.orbit.body.reference_frame), 'speed')
vessel_apoapsis_stream = conn.add_stream(getattr, vessel.orbit, 'apoapsis_altitude')

print('Launch!')
vessel.control.activate_next_stage()
first_stage_fuel_amount = vessel.resources_in_decouple_stage(2).amount
first_stage_fuel_amount_stream = conn.add_stream(first_stage_fuel_amount, 'LiquidFuel')

heights = []
speeds = []


def vessel_to_orbite(heading_start, heading_end, seconds_wait):
    for i in range(heading_start - heading_end + 1):
        vessel.auto_pilot.target_pitch_and_heading(heading_start - i, 90)
        time.sleep(seconds_wait)


while vessel_height_stream() < 27500.0:
    heights.append(vessel_height_stream())
    speeds.append(vessel_speed_stream())

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
        vessel_to_orbite(65, 60, 0.8)

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
    heights.append(vessel_height_stream())
    speeds.append(vessel_speed_stream())

    time.sleep(0.05)

print("Вторая ступень вышла из атмосферы, теперь можно переключиться на первую")
vessel.control.throttle = 0

vessel_height_stream.remove()
vessel_speed_stream.remove()
first_stage_fuel_amount_stream.remove()
