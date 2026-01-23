"""
MIT License

Copyright (c) 2017 - Present PythonistaGuild

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

OVERLAY_HTML = """<html>
    <body>
        <main id="container"></main>
        <script>
            const WSAddr = {WEBSOCKET_ADDR};
            const timeout = {TIMEOUT};

            let isConnected = false;
            let sock = new WebSocket(WSAddr);
            let reconnectInterval = null;
            let pingInterval = null;

            const setup = () => {{
                if (reconnectInterval !== null) {{
                    clearReconnect();
                }};

                sock.addEventListener("open", (e) => {{
                    console.log("Websocket connection successfully opened.");

                    clearReconnect();

                    if (pingInterval === null) {{
                    pingInterval = setInterval(pingTask, 10000);
                    }};
                }});

                sock.addEventListener("close", (e) => {{
                    console.log("Websocket connection closed.");
                    isConnected = false;

                    if (pingInterval !== null) {{
                        clearInterval(pingInterval);
                        pingInterval = null;
                    }};

                    // Try to re-establish connection...
                    reconnectInterval = setInterval(reconnect, timeout);
                }});

                sock.addEventListener("message", (e) => {{
                    const data = JSON.parse(e.data);
                    let nodes = data["nodes"];
                    let delay = data["duration"];

                    let container = document.getElementById("container");

                    for (let node of nodes) {{
                        console.log(node["raw"]);
                        container.insertAdjacentHTML("beforeend", node["raw"]);

                        if (node["type"] === "audio") {{
                            let audio = document.getElementById(node["html_id"]);
                            audio.play();
                        }};
                    }};
                }});
            }};

            const clearOverlay = () => {{
                let container = document.getElementById("container");
                container.innerHTML = "";
            }};

            const clearReconnect = () => {{
                clearInterval(reconnectInterval);
                reconnectInterval = null;
                isConnected = true;
            }};

            const pingTask = () => {{
               sock.send("ping");
            }};

            const reconnect = () => {{
                console.log("Attempting to reconnect to websocket.");

                if (isConnected) {{
                    clearReconnect();
                    return
                }};

                try {{
                    sock = new WebSocket(WSAddr);
                }} catch (error) {{
                    console.error("Unable to connect to websocket.");
                    return
                }};

                setup();
            }};

            setup();
        </script>
    </body>
</html>"""
