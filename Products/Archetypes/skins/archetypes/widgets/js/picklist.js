function pick_selectAllWords(theList) {
  myList = document.getElementById(theList)
    for (var x=0; x < myList.length; x++) {
      myList[x].selected="selected"
    }
}

function pick_addNewKeyword(toList,newText,newValue) {
  theToList=document.getElementById(toList);
  for (var x=0; x < theToList.length; x++) {
    if (theToList[x].text == newText) {
      return false;
    }
  }
  theLength = theToList.length;
  theToList[theLength] = new Option(newText);
  theToList[theLength].value = newValue;
}

function pick_moveKeywords(fromList,toList,selectThese) {
  theFromList=document.getElementById(fromList);
  for (var x=0; x < theFromList.length; x++) {
    if (theFromList[x].selected) {
      pick_addNewKeyword(toList, theFromList[x].text, theFromList[x].value);
    }
  }
  pick_selectAllWords(selectThese);
}

function pick_removeKeywords(theList,selectThese) {
  theToList=document.getElementById(theList);
  for (var x=theToList.length-1; x >= 0 ; x--) {
    if (theToList[x].selected) {
      theToList[x] = null;
    }
  }
  pick_selectAllWords(selectThese);
}
