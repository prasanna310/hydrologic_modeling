var allRectangles = [];
var allMarkers = [];
var map; // global variable
var drawingManager;
$(document).ready(function() {
    // Draw marker on text change
    $("#outlet_x").bind('input', drawMarkerOnTextChange);
    $("#outlet_y").bind('input', drawMarkerOnTextChange);
    // Draw rectangle on text change
    $("#box_topY").bind('input', drawRectangleOnTextChange);
    $("#box_bottomY").bind('input', drawRectangleOnTextChange);
    $("#box_rightX").bind('input', drawRectangleOnTextChange);
    $("#box_leftX").bind('input', drawRectangleOnTextChange);
    // ajax call function to submit the form
//    var user_form = $('#user-form');
//    user_form.submit(function() {
//        $('#submit-response').hide();
//        $('#submit-model-input-btn').prop('disabled', true);
//        // $('#wait').modal('show');
//        $.ajax({
//            type: user_form.attr('method'),
//            url: user_form.attr('action'),
//            data: user_form.serialize(),
//            success: function(result) {
//                console.log(result);
//                json_response = JSON.parse(result);
//                console.log(json_response);
//                // alert('happy');
//                $('#submit-response').show()
//                if (json_response.status == 'Error') {
//                    document.getElementById("submit-response").style.backgroundColor = '#ffebe6';
//                } else {
//                    document.getElementById("submit-response").style.backgroundColor = '#eafaea';
//                }
//                $('#response-status').text(json_response.status)
//                $('#response-result').text(json_response.result);
//            },
//            error: function() {
//                // alert('sad');
//                $('#submit-response').show();
//                document.getElementById("submit-response").style.backgroundColor = '#ffebe6';
//                $('#response-status').text('Error')
//                $('#response-result').text('Failed to run the web service. Please try it again.');
//            },
//            complete: function() {
//                // alert('complete');
//                $('#wait').modal('hide');
//                $('#submit-model-input-btn').prop('disabled', false);
//            }
//        });
//        return false;
//    });
});

function initMap() {
    var mapDiv = document.getElementById('map');
    map = new google.maps.Map(mapDiv, {
        center: {
            lat: 37.09024,
            lng: -95.712891
        },
        zoom: 9,
    });
    map.setMapTypeId('terrain');
    var drawingManager = new google.maps.drawing.DrawingManager({
        drawingControl: true,
        drawingControlOptions: {
            position: google.maps.ControlPosition.TOP_CENTER,
            drawingModes: [
                google.maps.drawing.OverlayType.MARKER,
                google.maps.drawing.OverlayType.RECTANGLE
            ]
        },
        rectangleOptions: {
            editable: true,
            draggable: true
        },

        markerOptions: {
            editable:true,
            draggable: true
        }
    });
    drawingManager.setMap(map);
	
    google.maps.event.addListener(drawingManager, 'rectanglecomplete', function(rectangle) {
        for (var i = 0; i < allRectangles.length; i++) {
            allRectangles[i].setMap(null);
        };



        var coordinates = (rectangle.getBounds());
        processDrawing(coordinates, 'rectangle');
        rectangle.addListener('bounds_changed', function() {
            var coordinates = (rectangle.getBounds());
            processDrawing(coordinates, "rectangle");


        });
    });
    google.maps.event.addListener(drawingManager, 'markercomplete', function(marker) {
        for (var i = 0; i < allMarkers.length; i++) {
            allMarkers[i].setMap(null);
        };
        var coordinates = (marker.getPosition());
        processDrawing(coordinates, 'marker');
        allMarkers.push(marker);

        //added so that when the marker is dragged it gets redrawn
        marker.addListener( "dragend", function(){
            var coordinates = (marker.getPosition());
            processDrawing(coordinates, 'marker');
        });
    });

	

    drawRectangleOnTextChange();
    drawMarkerOnTextChange();





    // block for places

    // Create the search box and link it to the UI element.
    var input = document.getElementById('pac-input');
    var searchBox = new google.maps.places.SearchBox(input);
    map.controls[google.maps.ControlPosition.TOP_LEFT].push(input);

    // Bias the SearchBox results towards current map's viewport.
    map.addListener('bounds_changed', function() {
      searchBox.setBounds(map.getBounds());
    });

    var markers = [];
    // Listen for the event fired when the user selects a prediction and retrieve
    // more details for that place.
    searchBox.addListener('places_changed', function() {
      var places = searchBox.getPlaces();

      if (places.length == 0) {
        return;
      }

      // Clear out the old markers.
      markers.forEach(function(marker) {
        marker.setMap(null);
      });
      markers = [];

      // For each place, get the icon, name and location.
      var bounds = new google.maps.LatLngBounds();
      places.forEach(function(place) {
        if (!place.geometry) {
          console.log("Returned place contains no geometry");
          return;
        }
        var icon = {
          url: place.icon,
          size: new google.maps.Size(71, 71),
          origin: new google.maps.Point(0, 0),
          anchor: new google.maps.Point(17, 34),
          scaledSize: new google.maps.Size(25, 25)
        };

        // Create a marker for each place.
        markers.push(new google.maps.Marker({
          map: map,
          icon: icon,
          title: place.name,
          position: place.geometry.location
        }));

        if (place.geometry.viewport) {
          // Only geocodes have viewport.
          bounds.union(place.geometry.viewport);
        } else {
          bounds.extend(place.geometry.location);
        }
      });
      map.fitBounds(bounds);
    });





//    initAutocomplete();
} // end of initmap function

function processDrawing(coordinates, shape) {
    if (shape == "rectangle") {
        // get coordinate value
        var bounds = {
            north: parseFloat(coordinates.getNorthEast().lat()),
            south: parseFloat(coordinates.getSouthWest().lat()),
            east: parseFloat(coordinates.getNorthEast().lng()),
            west: parseFloat(coordinates.getSouthWest().lng())
        };
        // collapse form for bounding box
        $('[id^=collapse]').removeClass('in')
        $('#collapse1').addClass('in')
        $('#collapse1').attr('style', '')
        // update form fields
        $("#box_topY").val(bounds.north.toFixed(4));
        $("#box_bottomY").val(bounds.south.toFixed(4));
        $("#box_rightX").val(bounds.east.toFixed(4));
        $("#box_leftX").val(bounds.west.toFixed(4));
    } else {
        // collapse form for outlet point
        $('[id^=collapse]').removeClass('in')
        $('#collapse3').addClass('in')
        $('#collapse3').attr('style', '')
        // update form fields
        $("#outlet_x").val(parseFloat(coordinates.lng()).toFixed(4));
        $("#outlet_y").val(parseFloat(coordinates.lat()).toFixed(4));
    }
} // end of processingDrawing function

function drawMarkerOnTextChange() {
    var myLatLng = {
        lat: parseFloat($("#outlet_y").val()),
        lng: parseFloat($("#outlet_x").val())
    };
    // Delete previous drawings
    for (var i = 0; i < allMarkers.length; i++) {
        allMarkers[i].setMap(null);
    };
    // Bounds validation
    var badInput = false;
    if (myLatLng.lat > 90 || myLatLng.lat < -90) {
        alert('Latitude should between -90 and 90 degree');
        $("#outlet_y").val('');
        badInput = true;
    }
    if (myLatLng.lng > 180 || myLatLng.lng < -180) {
        alert('Longitude should between -180 and 180 degree');
        $("#outlet_x").val('');
        badInput = true;
    }
    if (badInput || isNaN(myLatLng.lat) || isNaN(myLatLng.lng)) {
        return;
    }
    // Define the marker
    var marker = new google.maps.Marker({
        position: myLatLng,
        map: map
    });
    map.setCenter(marker.getPosition());
    allMarkers.push(marker);
} // end of drawMarkerOnTextChange
function drawRectangleOnTextChange() {
    var bounds = {
        north: parseFloat($("#box_topY").val()),
        south: parseFloat($("#box_bottomY").val()),
        east: parseFloat($("#box_rightX").val()),
        west: parseFloat($("#box_leftX").val())
    };
    // Delete previous drawings
    for (var i = 0; i < allRectangles.length; i++) {
        allRectangles[i].setMap(null);
    };
    // Bounds validation
    var badInput = false;
    // North
    if (bounds.north > 90 || bounds.north < -90) {
        alert('Latitude should between -90 and 90 degree');
        badInput = true;
        $("#box_topY").val('');
    }
    // East
    if (bounds.east > 180 || bounds.east < -180) {
        alert('Longitude should between -180 and 180 degree');
        badInput = true;
        $("#box_rightX").val('');
    }
    // South
    if (bounds.south < -90 || bounds.south > 90) {
        alert('Latitude should between -90 and 90 degree');
        badInput = true;
        $("#box_bottomY").val('');
    }
    // West
    if (bounds.west < -180 || bounds.west > 180) {
        alert('Longitude should between -180 and 180 degree');
        badInput = true;
        $("#box_leftX").val('');
    }
    if (badInput || isNaN(bounds.north) || isNaN(bounds.south) || isNaN(bounds.east) || isNaN(bounds.west)) {
        return;
    }
    // Define the rectangle and set its editable property to true.
    var rectangle = new google.maps.Rectangle({
        bounds: bounds,
        editable: true,
        draggable: true
    });
    rectangle.setMap(map);
    rectangle.addListener('bounds_changed', function() {
        var coordinates = (rectangle.getBounds());
        processDrawing(coordinates, "rectangle");
    });
    var southWest = new google.maps.LatLng(bounds.south, bounds.west);
    var northEast = new google.maps.LatLng(bounds.north, bounds.east);
    var bounds = new google.maps.LatLngBounds(southWest, northEast);
    // map.fitBounds(bounds);
    allRectangles.push(rectangle);
}


// This block of code for trying to uncheck download btns
var allRadios = document.getElementsByName('download_choice');
var booRadio;
var x = 0;
for (x = 0; x < allRadios.length; x++) {

    allRadios[x].onclick = function() {
        if (booRadio == this) {
            this.checked = false;
            booRadio = null;
        } else {
            booRadio = this;
        }
    };
}





















function mToDegree(distance_in_m, avg_lat){

			var R = 6371000; // in meters
			// var avg_lat = (document.forms["inputs"]["box_topY"].value + document.forms["inputs"]["box_bottomY"].value)/2 * 3.14/180;
			//var lon = (document.forms["inputs"]["box_rightX"].value +document.forms["inputs"]["box_leftX"].value) /2 * 3.14/180;
			var angle_along_lat =Math.abs(   distance_in_m / R * 180 /3.14 );
			var angle_along_lon =Math.abs(    distance_in_m / (R * Math.cos(avg_lat))* 180 /3.14 );
			return [angle_along_lon, angle_along_lat];
		}



window.geojson_callback = function(results) {
	 var map = new google.maps.Map(document.getElementById('map'), {
	 zoom: 9,
	 center: {lat: 42, lng: -111.3},
	 mapTypeId: 'terrain'
	  });

//    initMap();


    // I don't know how it works, but when a geojson is uploaded, I think the json string is added as
    // a variable in the script section as 'results'.
    // This will be loaded
	map.data.addGeoJson(results);
	if (results.features.length >1) {
		alert("Select feature class that contains just the one feature.")
		// :TODO make sure the file is ignored
	} else {

		var coords = results.features[0].geometry.coordinates[0];
		// :todo Make sure to see all the geojson. Because this is only valid for geographic CS
		var xmin = 180.0;
		var xmax = -180.0;
		var ymin = 90.0;
		var ymax = -90.0;
		for (var i = 0; i < coords.length; i++) {

//                    var coords = results.features[i].geometry.coordinates;
//                    var latLng = new google.maps.LatLng(coords[1], coords[0]);
			var x = coords[i][0];
			var y = coords[i][1];
			if (x < xmin) {xmin = x;}
			if (x > xmax) { xmax = x;}
			if (y < ymin) { ymin = y;}
			if (y > ymax) {ymax = y;}

		}
	}
	// Manage extent of the map, after the geojson is uploaded

            var cell = document.forms["inputs"]["cell_size"].value;
            xy = new Array();
            xy = mToDegree(cell, document.forms["inputs"]["box_bottomY"].value );
            var buffer  = 3;
            document.forms["inputs"]["box_bottomY"].value= ymin - buffer*xy[1] ;
            document.forms["inputs"]["box_leftX"].value=xmin - buffer*xy[0] ;
            document.forms["inputs"]["box_rightX"].value= xmax + buffer*xy[0] ;
            document.forms["inputs"]["box_topY"].value= ymax + buffer*xy[1];

            var new_center = new google.maps.LatLng( (ymin+ymax)/2 ,(xmin+xmax)/2);
            map.panTo(new_center);
            //google.maps.event.trigger(rectangle, 'bounds_changed');

			var marker2 = new google.maps.Marker({
				map:map,
//				position: new google.maps.LatLng( document.forms["inputs"]["outlet_y"].value , document.forms["inputs"]["outlet_x"].value),
				position: new_center, //google.maps.LatLng( document.forms["inputs"]["outlet_y"].value , document.forms["inputs"]["outlet_x"].value),

				draggable:true,
				label:"Outlet",
				scale: 10,
				//size : new google.maps.Size(21,34)

			});
			google.maps.event.addListener(marker2, "dragend", function(event){
				document.forms["inputs"]["outlet_x"].value= this.getPosition().lng() ;
				document.forms["inputs"]["outlet_y"].value= this.getPosition().lat() ;
			});

			var rectangle2 = new google.maps.Rectangle({
				map: map,
				bounds: new google.maps.LatLngBounds (
						new google.maps.LatLng(ymax+ buffer*xy[1],xmin- buffer*xy[0]),
						new google.maps.LatLng(ymin- buffer*xy[1],xmax+ buffer*xy[0])
				),
				fillColor:"grey",
				strokeColor:"blue",
				editable:true,
				draggable:true
			});

			google.maps.event.addListener(rectangle2, "bounds_changed", function(){
				var bounds = rectangle2.getBounds();
				var NE = bounds.getNorthEast();
				var SW = bounds.getSouthWest();

				document.forms["inputs"]["box_bottomY"].value= SW.lat() ;
				document.forms["inputs"]["box_leftX"].value= SW.lng();
				document.forms["inputs"]["box_rightX"].value= NE.lng();
				document.forms["inputs"]["box_topY"].value= NE.lat();

			});
//            document.getElementById('test_para').innerHTML = xmin.toString() + xmax.toString() + ymin.toString() + ymax.toString() ;
}























