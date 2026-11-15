importPackage(Packages.org.csstudio.opibuilder.scriptUtil);
var stamp = PVUtil.getTimeInMilliseconds(pvs[0]);
var label = "No GPS observation";
var tagged = pvs.length === 6;
if (stamp > 0 && PVUtil.getSeverity(pvs[0]) >= 0) {
    var status = PVUtil.getString(pvs[0]);
    label = (tagged ? "Check " + PVUtil.getLong(pvs[5]) + " · " : "") + status;
    if (status === "FIX") {
        var lat = PVUtil.getDouble(pvs[1]);
        var lon = PVUtil.getDouble(pvs[2]);
        var altitude = PVUtil.getDouble(pvs[3]);
        if (Math.abs(lat) <= 90 && Math.abs(lon) <= 180 && isFinite(altitude) && altitude > -2147483) {
            label += " · " + lat.toFixed(5) + "°, " + lon.toFixed(5) + "° · "
                + altitude.toFixed(1) + " m MSL · " + PVUtil.getLong(pvs[4]) + " satellites";
        }
    }
}
widget.setPropertyValue("text", label);
