const QUEUE = [];
const WS = new WebSocket(window.location + "/connect");
let isShowing = false;

WS.addEventListener("message", async (ev) => {
    let json;

    try {
        json = JSON.parse(ev.data);
    } catch (error) {
        console.error(`Error parsing JSON: ${error}.`);
        return;
    }

    const event = json.eventData;
    if (event.force_override || event.stack_event) {
        await displayData(json);
        return;
    }

    if (!isShowing) {
        await displayData(json);
    } else {
        QUEUE.push(json);
    }
});

WS.addEventListener("error", async (ev) => {
    console.log(ev);
});

async function prepareData(data) {
    const element = document.createElement("div");
    element.classList.add("eventContainer");

    for (const part of data.parts) {
        const content = part.content;
        const anim = part.animation || "";
        const speed = part.speed || "";
        const fontSize = part.size || 22;

        let html = `<span style="font-size: ${fontSize}px;" class="animate__animated animate__infinite${anim}${speed}">${content}</span>`;
        element.insertAdjacentHTML("beforeend", html);
    }

    return element;
}

async function displayData(data) {
    const event = data.eventData;
    isShowing = true;

    const prepared = await prepareData(event);
    const wrapper = document.getElementById("wrapper");
    
    wrapper.classList.remove(wrapper.classList.name);
    wrapper.classList.add(data.position);

    if (!wrapper) {
        console.error(`The <div> with the ID of "wrapper" cannot be found.`);
        return;
    }

    if (event.force_override) {
        await cleanState();
    }

    wrapper.insertAdjacentElement("afterbegin", prepared);

    if (event.duration !== null && event.duration > 0) {
        setTimeout(async () => {
            await endEvent(prepared);
        }, event.duration);
    }
}

async function cleanState() {
    // ...
}

async function endEvent(element) {
    element.remove();

    if (QUEUE.length <= 0) {
        isShowing = false;
        return;
    }

    const data = QUEUE.shift();
    await displayData(data);
    await sendCallback();
}

async function sendCallback() {
    try {
        await fetch(window.location + "/callback", { method: "POST", "body": "WOT" });
    } catch (error) {
        console.error(error);
    }
}