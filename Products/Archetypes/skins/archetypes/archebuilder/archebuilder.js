
function logMessage (logtitle, logtext) {

    // Send output messages somewhere besides alert boxes!
    // Easy to turn on/off, just set display: none in css
    var logger = document.getElementById("debuglog");
    // Do nothing we can't find the logger element
    if (!logger) {
        return;
    }

    // Create log message and insert in the beginning
    var now = new Date();
    now = now.getTime();
    var logmsg = document.createElement("label");
    logmsg.setAttribute("value", logtitle);
    logmsg.setAttribute("title", now + ": " + logtext);
    logger.insertBefore(logmsg, logger.firstChild);

    // Chop off any log messages after 5
    while (logger.getElementsByTagName("label").length > 5) {
	logger.removeChild(logger.lastChild);
    }
    return;       
}


function init () {
    ztxml = Sarissa.getDomDocument();
    ztxml.async = true;
    ztxsl = Sarissa.getDomDocument();
    ztxsl.async = true;

    function ztxslHandler () {
	if (ztxsl.readyState == 4 && ztxsl.xml) {
	    logMessage("XSLT file loaded and parsed");
	    runTransform();
	    return;
	}
    }

    function ztxmlHandler () {
	if (ztxml.readyState == 4 && ztxml.xml) {
	    logMessage("Project file loaded and parsed");
	    ztxsl.load("archebuilderxul.xsl");
	}
    }
    ztxml.onreadystatechange = ztxmlHandler;
    ztxsl.onreadystatechange = ztxslHandler;
    ztxml.setProperty("SelectionLanguage", "XPath");
    ztxsl.setProperty("SelectionLanguage", "XPath");
    ztxml.load("archetypes_ttw_tool/registry_xml");

    return;
}


function runTransform () {

    // transform and store the mainresults to containing HTML doc
    var mainresult = Sarissa.getDomDocument();
    ztxml.transformNodeToObject(ztxsl, mainresult);

    // Move the mainresult HTML to the browser window
    var body = document.getElementById("ab-main");
    var content = mainresult.getElementById("ab-main");

    if (_SARISSA_IS_MOZ) {
	newresult = document.importNode(content, true);
	body.replaceChild(newresult, body.firstChild);
    } else {
	body.innerHTML = mainresult.xml;
    }

    return;
}


function toggleExpand (evt) {
    if (!evt) {
	evt = window.event;
	evt.target = evt.srcElement;
    }
    
    // Grab the xml node for the clicked folder
    var targeturl = evt.target.id;
    var xpath = "/children//collection[@url='" + targeturl + "']";
    var expandnode = ztxml.selectSingleNode(xpath);

    // Change state and re-run transform
    if (expandnode.hasAttribute("isexpanded")) {
	expandnode.removeAttribute("isexpanded");
    } else {
	expandnode.setAttribute("isexpanded", "1");
	// Now test to see if we should load more data
	if (expandnode.childNodes.length == 0) {
	    // Grab more data
	    loadChildData("children.xml", expandnode);
	    return;
	}
    }
    runTransform();
    return;
}


function loadChildData (url, targetnode) {

    newdata = Sarissa.getDomDocument();
    newdata.async = true;
    function newdataHandler () {
	if (newdata.readyState == 4 && newdata.xml) {
	    // XXX make work w/ IE
	    var r = newdata.createRange();
	    r.selectNodeContents(newdata.documentElement);
	    var frag = r.cloneContents();
	    targetnode.appendChild(frag);
	    logMessage("New data loaded and attached");
	    runTransform();
	}
    }
    newdata.onreadystatechange = newdataHandler;
    newdata.load(url);
    return;
}
