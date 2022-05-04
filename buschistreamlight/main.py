#!/usr/bin/python

from fastapi import FastAPI, BackgroundTasks
from fastapi_utils.tasks import repeat_every
from math import sqrt
from requests import get, post
import asyncio
import os
import random
import serial
import time
import uvicorn


hass_api_token = os.getenv('HASS_API_TOKEN')
hass_domain = os.getenv('HASS_DOMAIN')
api_port = int(os.getenv('API_PORT', 8000))
serial_device_path = os.getenv('SERIAL_DEVICE', "/dev/ttyACM0")


app = FastAPI()
queue = asyncio.Queue()
loop = asyncio.get_event_loop()
current_pos = None
brightness_value = 150

neutral_pos = [800,-900]
up_value = -500
down_positions = [
    [450,-1400],
    [450,-1200],
    [1100,-1400],
    [1100,-1200],
]

in_view = False
light_states = {"lol": None, "alarm": None, "skull": None, "buschi": None, "b": None, "thumps_up": None, "thumps_down": None}
hass_light_api = "http://{}/api/services/light/{}"

headers = {
    "Authorization": f"Bearer {hass_api_token}",
    "content-type": "application/json",
}

def start():
    """Launched with `poetry run start` at root level"""
    uvicorn.run("buschistreamlight.main:app",
                host="0.0.0.0", port=api_port, reload=True)


def send_hass_request(url: str, data: str):
    response = post(url, headers=headers, json=data)
    print(url, data)
    return response.text


async def connect_buschi_cran():
    with serial.Serial() as ser:
        ser.baudrate = 115200
        ser.port = serial_device_path
        ser.open()
        while True:
            wp = await queue.get()
            cmd: str = f'G1 X{wp[0]} Y{wp[1]}'
            print(f'Sending {cmd}')
            ser.write(str.encode(cmd))


def send_wapoint(pos: list()) -> int:
    global current_pos
    print(pos)
    if current_pos:
        distance = sqrt(pow(current_pos[0]-pos[0], 2) +
                        pow(current_pos[1]-pos[1], 2))
    else:
        distance = None
    current_pos = pos
    queue.put_nowait(pos)
    return distance


@app.on_event("startup")
@repeat_every(seconds=1)
def check_timeout() -> None:
    global light_states, in_view
    for light in light_states.keys():
        if light_states[light] and time.time() > light_states[light]:
            light_states[light] = None
            data = {"entity_id": f"light.{light}"}
            send_hass_request(hass_light_api.format(
                hass_domain, "turn_off"), data)
    if in_view and not any(light_states.values()):
        in_view = False
        #send_wapoint([current_pos[0], up_value])
        send_wapoint(neutral_pos)


@app.on_event("startup")
async def startup() -> None:
    asyncio.create_task(connect_buschi_cran())
    check_timeout()


@app.get("/brightness/{value}")
def set_brightness(value: int):
    global brightness_value
    brightness_value = value
    return {"result": "success"}


@app.get("/{light}/{mode}")
def buschi_light(light: str, mode: str, timeout: int=None, color: str = None, brightness: int = None):
    global in_view

    if not light in light_states.keys():
        return {"error": "light source unknown"}
    if mode not in ["on", "off"]:
        return {"error": "mode unknown"}
    elif mode == "off":
        light_states[light] = None
    else:
        light_states[light] = time.time() + 36000

    if timeout:
        light_states[light] = time.time() + timeout

    if mode == "on" and not in_view:
        distance = send_wapoint(random.choice(down_positions))
        in_view = True

    if color:
        if len(color) != 6:
            return {"error": "color value erroneous"}
        else:
            rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
    else:
        rgb = (brightness or brightness_value,
               brightness or brightness_value, brightness or brightness_value)

    data = {"entity_id": f"light.{light}"}
    if mode == "on":
        data["rgb_color"] = rgb
        data["brightness"] = brightness or brightness_value
    
    result = send_hass_request(hass_light_api.format(hass_domain, "turn_" + mode), data)

    return {"result": "success", "hass_api_result": result}
