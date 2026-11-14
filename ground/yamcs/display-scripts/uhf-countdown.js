importPackage(Packages.org.csstudio.opibuilder.scriptUtil);
var stamp = PVUtil.getTimeInMilliseconds(pvs[0]);
var listen = PVUtil.getLong(pvs[1]) * 1000;
var telemetry = PVUtil.getLong(pvs[2]) * 1000;
var offset = PVUtil.getLong(pvs[3]);
var age = Date.now() - stamp;
var cycle = listen + telemetry;
var newBoot = PVUtil.getTimeInMilliseconds(pvs[5]) > stamp &&
    PVUtil.getLong(pvs[5]) !== PVUtil.getLong(pvs[4]);
var label = "UHF schedule · waiting for current IHU status";
if (stamp > 0 && !newBoot && age >= -5000 && age <= cycle + 30000 && listen > 0 &&
    telemetry > 0 && offset >= 0 && offset < cycle) {
    if (PVUtil.getLong(pvs[0]) === 0) {
        label = "UHF schedule off · scheduled telemetry quiet";
    } else {
        var phase = (offset + Math.max(0, age)) % cycle;
        var listening = phase < listen;
        var seconds = Math.ceil(((listening ? listen : cycle) - phase) / 1000);
        var countdown = Math.floor(seconds / 60) + ":" + ("0" + seconds % 60).slice(-2);
        label = listening ? "IHU LISTEN · ~" + countdown + " until telemetry" :
            "IHU TELEMETRY · ~" + countdown + " until listen";
        label += "  (" + listen / 1000 + " s / " + telemetry / 1000 + " s)";
    }
}
widget.setPropertyValue("text", label);
