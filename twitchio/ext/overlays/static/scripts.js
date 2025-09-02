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

    const anim = data.animation;
    const speed = data.speed;

    if (anim) {
        element.classList.add("animate__animated", anim);
    }
    if (speed) {
        element.classList.add(speed);
    }

    for (const part of data.parts) {
        let img, iw, ih;

        const isImg = part.is_image;
        const content = part.content;
        const anim = part.animation || "";
        const speed = part.speed || "";
        const fontSize = part.size || 22;
        const colour = part.colour || "#000";
        const align = part.alignment || "s";

        if (isImg) {
            img = await prepareImg(part.content);
        }

        if (img) {
            if (part.dimensions) {
                [iw, ih] = part.dimensions;
                img.style.width = `${iw}px`;
                img.style.height = `${ih}px`;
            }

            img.classList.add("animate__animated");
            anim ? img.classList.add(anim.trim()) : null;
            speed ? img.classList.add(speed.trim()) : null;
            align ? img.classList.add(align.trim()) : null;

            element.insertAdjacentElement("beforeend", img);
            continue;
        }

        let html = `<span 
                        style="font-size: ${fontSize}px;color: ${colour};"
                        class="animate__animated animate__infinite${anim}${speed}${align}"
                    >
                        ${content}
                    </span>`;
        element.insertAdjacentHTML("beforeend", html);
    }

    return element;
}

async function prepareAudio(uri) {
    if (!uri) { return null }
    let url;

    try {
        // Check if audio is an exisiting URL...
        url = new URL(uri);
    } catch (_) {
        url = new URL(`${window.location}/audio/${uri}`);
    }

    if (url.protocol !== "http:" && url.protocol !== "https:") {
        return null
    }

    const audio = new Audio(url);
    return audio;
}

async function prepareImg(uri) {
    if (!uri) { return null }
    let url;

    try {
        // Check if image is an exisiting URL...
        url = new URL(uri);
    } catch (_) {
        url = new URL(`${window.location}/image/${uri}`);
    }

    if (url.protocol !== "http:" && url.protocol !== "https:") {
        return null
    }

    const img = document.createElement("img");
    img.src = url.href;
    img.classList.add("eventImg");

    return img;
}

async function displayData(data) {
    const event = data.eventData;
    isShowing = true;

    const prepared = await prepareData(event);
    const wrapper = document.getElementById("wrapper");
    if (!wrapper) {
        console.error(`The <div> with the ID of "wrapper" cannot be found.`);
        return;
    }

    wrapper.classList.remove(wrapper.classList.name);
    wrapper.classList.add(data.position);

    if (event.force_override) {
        await cleanState();
    }

    wrapper.insertAdjacentElement("afterbegin", prepared);

    const audio = await prepareAudio(event.audio);
    if (audio) {
        audio.volume = event.volume || 50;
        audio.play();

        if (event.duration_is_audio) {
            audio.addEventListener("ended", async () => {
                await endEvent(prepared);
            });

            return;
        }
    }

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