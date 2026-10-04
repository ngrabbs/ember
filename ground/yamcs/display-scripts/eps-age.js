importPackage(Packages.org.csstudio.opibuilder.scriptUtil);
var age = PVUtil.getLong(pvs[0]);
widget.setPropertyValue("text", PVUtil.getSeverity(pvs[0]) < 0 ? "EPS packet expired; UART readout age unknown" : age === 4294967295 ? "No complete PEC-checked UART readout received" : "Last good UART readout: " + (age / 1000).toFixed(1) + " s before this packet • repeats are not new ADC samples");
