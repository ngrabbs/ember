importPackage(Packages.org.csstudio.opibuilder.scriptUtil);
var sha = "";
for (var i=0;i<5;i++) {var h=Number(PVUtil.getDouble(pvs[i])).toString(16);sha += ("00000000"+h).slice(-8);}
widget.setPropertyValue("text", sha);
