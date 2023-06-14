import asyncio

class MyUDPServerProtocol(asyncio.DatagramProtocol):
    def __init__(self, data_received_callback):
        self.data_received_callback = data_received_callback

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        self.data_received_callback(data, addr, self.send_response)

    def send_response(self, data, addr):
        self.transport.sendto(data, addr)

async def start_udp_server(endpoint, data_received_callback):
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: MyUDPServerProtocol(data_received_callback),
        local_addr=endpoint
    )
    print(f"UDP server started on {endpoint}")
    try:
        await asyncio.Event().wait()
    finally: 
        transport.close()

async def start_udp_servers(data_received_callback):
    # Define server endpoints (host, port)
    endpoints = [
        ('0.0.0.0', 52381),
        ('0.0.0.0', 1259)
    ]

    tasks = [start_udp_server(endpoint, data_received_callback) for endpoint in endpoints]
    await asyncio.gather(*tasks)
