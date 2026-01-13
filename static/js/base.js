// static/js/base.js
document.addEventListener("DOMContentLoaded", function () {
    const panel = document.getElementById("stationPanel");
    if (!panel) return; // page does not have the panel

    const handle = panel.querySelector(".drag-handle");
    if (!handle) return;

    let isDragging = false;
    let offsetX = 0;
    let offsetY = 0;

    handle.addEventListener("mousedown", function (e) {
        isDragging = true;

        const rect = panel.getBoundingClientRect();
        offsetX = e.clientX - rect.left;
        offsetY = e.clientY - rect.top;

        panel.style.transition = "none";
        panel.style.right = "auto";
        document.body.style.userSelect = "none";
    });

    document.addEventListener("mousemove", function (e) {
        if (!isDragging) return;

        panel.style.left = `${e.clientX - offsetX}px`;
        panel.style.top = `${e.clientY - offsetY}px`;
    });

    document.addEventListener("mouseup", function () {
        if (!isDragging) return;

        isDragging = false;
        document.body.style.userSelect = "";
    });
});
