/*
  More namespacelike code for the webgl visualisation
*/
function SurgeryWebGLVisualiser() {
    //the div holding the canvas
    this.container = null;

    this.camera = undefined;
    this.controls = undefined;
    this.scene = null;
    this.renderer = undefined;
    this.material = undefined;

    /*
      objects used to generate the defects 
    */
    this.primalDefects = null;
    this.dualDefects = null;
    this.notWorkingDefect = null;
    this.debugDefects1 = null;
    this.debugDefects2 = null;

    /*
      objects in the plumbing piece scene
    */
    this.plumbingUnits = undefined;
    this.plumbingPrimals = undefined;
    this.plumbingDuals = undefined;

    /*
      objects in the defects piece scene
    */
    this.primalGeometry = null;
    this.primalGeometry2 = null;
    this.dualGeometry = null;
    this.dualGeometry2 = null;
    this.boxesGeometry = null;
    this.defectBoundingBox = null;

    /*Materials*/
    this.materialPrimal = new THREE.LineBasicMaterial({ color: /*0xFF0000*/0x181919, linewidth: 4, transparent: true, opacity: 1 });
    this.materialPrimal2 = new THREE.LineBasicMaterial({ color: /*0xFF0000*/0xfcf2f3, linewidth: 2, transparent: true, opacity: 1 });

    this.materialDual = new THREE.LineBasicMaterial({ color: /*0x0000FF*/0x181919, linewidth: 8, transparent: true, opacity: 1 });
    this.materialDual2 = new THREE.LineBasicMaterial({ color: /*0x0000FF*/0x686565, linewidth: 6, transparent: true, opacity: 1 });

    this.materialInjection = new THREE.MeshLambertMaterial({ color: "green" });
    this.materialNotWorking = new THREE.LineBasicMaterial({ color: 0xFFFF00, linewidth: 20, transparent: false, opacity: 1 });
    this.materialDebug1 = new THREE.LineBasicMaterial({ color: 0x00FF00, linewidth: 5, transparent: false, opacity: 1 });
    this.materialDebug2 = new THREE.LineBasicMaterial({ color: 0xf442eb, linewidth: 5, transparent: false, opacity: 1 });

    /*bounding box*/
    this.bBox = null;
    this.resetBoundingBox();

    /*statistics*/
    // this.stats = new Stats();
    this.objectsToClick = [];

    /*standby render*/
    this.renderLastMove = Date.now();
    this.renderRunning = false;
    this.renderStandbyAfter = 2000; // ms

    /*defect visualisation parameters*/
    this.drawBoxes = true;
    this.drawGeometry = true;
    this.drawPrimals = true;
    this.drawDuals = true;

    /*
        Dec. 2018: for lattice surgery
    */
    this.lattice_meshes = [];
}

/*
    asta nu are ce cauta aici. este legata de HTML
*/
SurgeryWebGLVisualiser.prototype.readGetParameters = function () {
    var GET = {};
    var query = window.location.search.substring(1).split("&");
    for (var i = 0, max = query.length; i < max; i++) {
        if (query[i] === "") // check for trailing & with no param
            continue;

        var param = query[i].split("=");
        if (param.length == 1) {
            GET[decodeURIComponent(param[0])] = 1;
        }
        else {
            GET[decodeURIComponent(param[0])] = decodeURIComponent(param[1] || "");
        }
    }

    if (GET.noboxes) {
        this.drawBoxes = false;
    }
    if (GET.nogeom) {
        this.drawGeometry = false;
    }
    if (GET.noprimals) {
        this.drawPrimals = false;
    }
    if (GET.noduals) {
        this.drawDuals = false;
    }
}

SurgeryWebGLVisualiser.prototype.deleteAllSceneRelated = function () {
    this.container.innerHTML = "";
    this.scene = null;
}

// ************ STARTUP *****************
SurgeryWebGLVisualiser.prototype.start_defect_view = function (gr1, gr2, gr3, gr4, bx0) {

    this.readGetParameters();

    if (this.scene == null) {
        this.pre_init();
    }
    else {
        this.scene.remove(this.primalGeometry);
        this.scene.remove(this.primalGeometry2);
        this.scene.remove(this.dualGeometry);
        this.scene.remove(this.dualGeometry2);
        this.scene.remove(this.boxesGeometry);
        this.scene.remove(this.defectBoundingBox);

        this.primalGeometry.geometry.dispose();
        this.primalGeometry2.geometry.dispose();
        this.dualGeometry.geometry.dispose();
        this.dualGeometry2.geometry.dispose();
        this.boxesGeometry.geometry.dispose();
        this.defectBoundingBox.geometry.dispose();

        this.primalGeometry = null;
        this.primalGeometry2 = null;
        this.dualGeometry = null;
        this.dualGeometry2 = null;
        this.boxesGeometry = null;
        this.defectBoundingBox = null;

        this.resetBoundingBox();
        this.removeAllSpheres();
    }

    /*
        tmp construct
    */
    this.primalDefects = new THREE.Geometry();
    this.dualDefects = new THREE.Geometry();
    this.notWorkingDefect = new THREE.Geometry();
    this.debugDefects1 = new THREE.Geometry();
    this.debugDefects2 = new THREE.Geometry();

    if (this.camera.position.x == 0 && this.camera.position.y == 0 && this.camera.position.z == 10) {
        // Center the camera
        var sx = 0; var sy = 0; var sz = 0;
        for (var i = 0; i < gr1.nodes.length; ++i) {
            var n = gr1.nodes[i];
            if (n[1] > sx) { sx = n[1]; }
            if (n[2] > sy) { sy = n[2]; }
            if (n[3] > sz) { sz = n[3]; }
        }
        this.camera.position.set(sx / 2, sy / 2, sz + sx * 5);
        this.controls.target.set(sx / 2, sy / 2, sz / 2 - sx * 1.5);
    }

    if (this.drawBoxes) {
        // console.log(bx0);
        this.boxesGeometry = this.makeBoxes(bx0);
        this.scene.add(this.boxesGeometry);

        //this.makeBoxes(boxes1);
        //this.makeBoxes(boxes2);
    }

    this.makeGeometry(gr1, null);//the circuit
    this.makeGeometry(gr2, null);//connects pins to boxes
    this.makeGeometry(gr3, this.debugDefects1 /*all is in debug*/);
    this.makeGeometry(gr4, this.debugDefects2 /*all is in debug*/);

    //makeLineSegments(makebuffered(debugDefects1), materialDebug1);
    // makeLineSegments(makebuffered(debugDefects2), materialDebug2);
    // makeLineSegments(makebuffered(notWorkingDefect), materialNotWorking);

    this.primalGeometry = this.makeLineSegments(this.makeBuffered(this.primalDefects), this.materialPrimal)[0];
    this.primalGeometry2 = this.makeLineSegments(this.makeBuffered(this.primalDefects), this.materialPrimal2)[0];

    this.dualGeometry = this.makeLineSegments(this.makeBuffered(this.dualDefects), this.materialDual)[0];
    this.dualGeometry2 = this.makeLineSegments(this.makeBuffered(this.dualDefects), this.materialDual2)[0];

    if (this.drawPrimals) {
        this.scene.add(this.primalGeometry);
        this.scene.add(this.primalGeometry2);
    }

    if (this.drawDuals) {
        this.scene.add(this.dualGeometry);
        this.scene.add(this.dualGeometry2);
    }

    this.defectBoundingBox = this.makeBoundingBox();
    this.scene.add(this.defectBoundingBox);

    /*
        destruct
    */
    this.primalDefects.dispose();
    this.dualDefects.dispose()
    this.notWorkingDefect.dispose()
    this.debugDefects1.dispose()
    this.debugDefects2.dispose()

    this.primalDefects = null;
    this.dualDefects = null;
    this.notWorkingDefect = null;
    this.debugDefects1 = null;
    this.debugDefects2 = null;

    this.animate(this);

    /*http://stackoverflow.com/questions/32955103/selecting-object-with-mouse-three-js*/
    /*select new defect : mouse down + click*/
    /*
    //linePrimal and lineDual disappered from the code
    objectsToClick = [linePrimal, lineDual];
    
    renderer.domElement.addEventListener( 'mousedown', onDocumentMouseDown );
    function onDocumentMouseDown( event ) 
    {
      if (!event.shiftKey)
      {
        return;
      }
      
      event.preventDefault();
      var found = false;
      //dimension of the mouse coordinate window to search
      var dim = 5;
      for(var i=-dim/2; i<dim/2+1 && !found; i++)
      {
        for(var j=-dim/2; j<dim/2+1 && !found; j++)
        {
          found = mouse3dray(event.clientX + i, event.clientY + j);
        }
      }
      
      if(found)
      {
        //linePrimal.material.color.setHex( Math.random() * 0xffffff );
        linePrimal.material.opacity = 0.5;
      }
      else
      {
        linePrimal.material.opacity = 1;
      }
    }    
    */
}

SurgeryWebGLVisualiser.prototype.addSphere = function (x, y, z, material) {

    var sphere = new THREE.Mesh(this.spheregeometry, material);
    sphere.position.x = x;
    sphere.position.y = y;
    sphere.position.z = z;

    this.scene.add(sphere);

    this.spheres.push(sphere);
}

SurgeryWebGLVisualiser.prototype.removeAllSpheres = function () {
    for (var i = 0; i < this.spheres.length; i++) {
        this.scene.remove(this.spheres[i]);

        //do not call dispose because it will invalidate the sphere geometry
        //this.spheres[i].dispose();

        //lose the reference
        this.spheres[i] = null;
    }

    this.spheres = [];
}

SurgeryWebGLVisualiser.prototype.add_edge2 = function (x1, y1, z1, x2, y2, z2, lineSegmentsGeometry) {
    lineSegmentsGeometry.vertices.push(new THREE.Vector3(x1, y1, z1));
    lineSegmentsGeometry.vertices.push(new THREE.Vector3(x2, y2, z2));

    this.updateBoundingBox(x1, y1, z1);
    this.updateBoundingBox(x2, y2, z2);
}

SurgeryWebGLVisualiser.prototype.add_edge2Index = function (index, graphobject, lineSegmentsGeometry) {
    var a = graphobject.nodes[graphobject.edges[index][0] - 1];
    var b = graphobject.nodes[graphobject.edges[index][1] - 1];

    this.add_edge2(a[1], a[2], a[3], b[1], b[2], b[3], lineSegmentsGeometry);
}

SurgeryWebGLVisualiser.prototype.makePins = function (boxparam, bigcube) {
    var geometry = new THREE.BoxGeometry(1, 1, 1);

    for (var i = 0; i < 2; i++) {
        var cube = new THREE.Mesh(geometry, new THREE.MeshBasicMaterial({
            color: 'red'
        }));

        cube.position.x = 0.5/*coordonata nu colt ci centrul*/
            + boxparam[2] + boxes.types[boxparam[1]][0] - (1 - i) * 2 * 2/*dist*/ - 1/*acuma e cu o unitate prea in dreapta*/;
        cube.position.y = 0.5 + boxparam[3] + boxes.types[boxparam[1]][1] - 1/*acuma e cu o unitate prea in sus*/;
        cube.position.z = 0.5 + boxparam[4] + boxes.types[boxparam[1]][2];

        this.scene.add(cube);
    }
}

SurgeryWebGLVisualiser.prototype.makeBoxes = function (sched) {
    var boxes = new THREE.Geometry();

    for (var i = 0; i < sched.coords.length; i++) {
        var boxparam = sched.coords[i];
        var width = sched.types[boxparam[0]][0];
        var height = sched.types[boxparam[0]][1];
        var depth = sched.types[boxparam[0]][2];

        var geometry = new THREE.BoxGeometry(width, height, depth);

        geometry.translate(boxparam[2] + width / 2,
            boxparam[3] + height / 2,
            boxparam[4] + depth / 2);

        //for box start coordinates
        this.updateBoundingBox(boxparam[2], boxparam[3], boxparam[4]);
        //include box dimensions, too
        this.updateBoundingBox(boxparam[2] + width, boxparam[3] + height, boxparam[4] + depth);

        var cube = new THREE.Mesh(geometry);
        cube.updateMatrix();

        boxes.merge(cube.geometry, cube.matrix);
        cube = null;

		/*debugMessage(i+"b", boxparam[2] + geometry.parameters.width/2,
		                    boxparam[3] + geometry.parameters.height/2,
		                    boxparam[4] + geometry.parameters.depth/2);*/
    }

    var cubes = new THREE.Mesh(boxes,

        //new THREE.MeshBasicMaterial({wireframe: true, color: 'green'})

        new THREE.MeshLambertMaterial({ color: 'green', side: THREE.DoubleSide, shading: THREE.FlatShading })
    );

    return cubes;
}

SurgeryWebGLVisualiser.prototype.debugMessage = function (message, x, y, z) {
    var s1 = makeTextSprite2(message);

    s1.position.x = x;
    s1.position.y = y;
    s1.position.z = z;

    this.scene.add(s1);
}

SurgeryWebGLVisualiser.prototype.findPoint = function (point, graphobject, objToFill) {
    //make edges
    var found = false;
    var i = -1;
    for (i = 0; i < graphobject.edges.length && !found; i++) {
        var a = graphobject.nodes[graphobject.edges[i][0] - 1];
        var b = graphobject.nodes[graphobject.edges[i][1] - 1];

        var eq = 0;
        var included = true;
        for (var j = 0; j < 3; j++) {
            var compj = point.getComponent(j);
            if (a[j + 1] == compj && b[j + 1] == compj) {
                eq++;
            }

            if (a[j + 1] < b[j + 1]) {
                included = (a[j + 1] <= compj) && (compj <= b[j + 1])
            }
            else if (a[j + 1] > b[j + 1]) {
                included = (b[j + 1] <= compj) && (compj <= a[j + 1])
            }
        }

        if (eq == 2 && included) {
            found = true;
            console.log("found");
            //add_edge2(a[1], a[2], a[3], b[1], b[2], b[3], notWorkingDefect);
        }
    }

    if (found) {
        var idx1 = graphobject.edges[i][0];
        var idx2 = graphobject.edges[i][1];

        this.add_edge2Index(i, graphobject, notWorkingDefect);

        for (var j = i + 1; j < graphobject.edges.length; j++) {
            if (graphobject.edges[j][0] == idx1) {
                idx1 = graphobject.edges[j][1];
                this.add_edge2Index(j, graphobject, notWorkingDefect);
            }
            else if (graphobject.edges[j][1] == idx1) {
                idx1 = graphobject.edges[j][0];
                this.add_edge2Index(j, graphobject, notWorkingDefect);
            }
            else if (graphobject.edges[j][0] == idx2) {
                idx2 = graphobject.edges[j][1];
                this.add_edge2Index(j, graphobject, notWorkingDefect);
            }
            else if (graphobject.edges[j][1] == idx2) {
                idx2 = graphobject.edges[j][0];
                this.add_edge2Index(j, graphobject, notWorkingDefect);
            }
        }

        for (var j = i - 1; j >= 0; j--) {
            if (graphobject.edges[j][0] == idx1) {
                idx1 = graphobject.edges[j][1];
                this.add_edge2Index(j, graphobject, notWorkingDefect);
            }
            else if (graphobject.edges[j][1] == idx1) {
                idx1 = graphobject.edges[j][0];
                this.add_edge2Index(j, graphobject, notWorkingDefect);
            }
            else if (graphobject.edges[j][0] == idx2) {
                idx2 = graphobject.edges[j][1];
                this.add_edge2Index(j, graphobject, notWorkingDefect);
            }
            else if (graphobject.edges[j][1] == idx2) {
                idx2 = graphobject.edges[j][0];
                this.add_edge2Index(j, graphobject, notWorkingDefect);
            }
        }

    }

    return found;
}

SurgeryWebGLVisualiser.prototype.makeGeometry = function (graphobject, objToFill) {

    //make injections
    for (var i = 0; i < graphobject.inj.length; i++) {
        var n = graphobject.nodes[graphobject.inj[i] - 1];
        this.addSphere(n[1], n[2], n[3], this.materialInjection);
    }

    //make edges
    for (var i = 0; i < graphobject.edges.length; i++) {
        var a = graphobject.nodes[graphobject.edges[i][0] - 1];
        var b = graphobject.nodes[graphobject.edges[i][1] - 1];

        if (objToFill != null) {
            //add_edge2(a[1], a[2], a[3], b[1], b[2], b[3], objToFill);
            this.add_edge2Index(i, graphobject, objToFill);
        }
        else {
            //if(otherside >= 2)//asta e pentru qubits si nu pentru celule. eu calculez in celule. in pula mea iar am incurcat...
            otherside = 0;
            for (var j = 1; j < 4; j++) {
                if (Math.abs(a[j]) % 2 != 0) {
                    otherside++;
                }
            }

            if (otherside == 3) {//celulele primare au coordonate impare, iar cele duale au coordonate pare
                //add_edge2(a[1], a[2], a[3], b[1], b[2], b[3], primalDefects);
                this.add_edge2Index(i, graphobject, this.primalDefects);
            }
            //else
            if (otherside == 0) {
                //add_edge2(a[1], a[2], a[3], b[1], b[2], b[3], dualDefects);
                this.add_edge2Index(i, graphobject, this.dualDefects);
            }

            if (i == graphobject.edges.length - 1) {
                //the connection that was not constructed should be highlighted with a dual segment
                //to be distinct from the green blocks
                //add_edge2(a[1], a[2], a[3], b[1], b[2], b[3], notWorkingDefect);
                this.add_edge2Index(i, graphobject, this.notWorkingDefect);
            }
        }
    }
}

SurgeryWebGLVisualiser.prototype.setup_visualisation = function (containername) {
    this.container = document.getElementById(containername);

    var d = document;
    var e = d.documentElement;
    var x = window.innerWidth || e.clientWidth || this.container.clientWidth;
    var y = window.innerHeight || e.clientHeight || this.container.clientHeight;

    var WIDTH = x;
    var HEIGHT = y;

    var oldstyle = this.container.getAttribute("style");
    oldstyle += "display:block; width:" + WIDTH + "px; height:" + (HEIGHT - 20) + "px;";
    this.container.setAttribute("style", oldstyle);

    this.container.style.width = WIDTH + 'px';
    this.container.style.height = (HEIGHT - 20) + 'px';

    // Models
    this.spheregeometry = new THREE.SphereGeometry(.5, 3, 3)

    var referenceToThis = this;

    this.container.addEventListener("mousedown",
        function () {
            // console.log("start" + containername);
            referenceToThis.renderRunning = false;
            referenceToThis.startAnimation(referenceToThis)
        }, true);
    this.container.addEventListener("mouseup",
        function () {
            // console.log("stop" + containername);
            referenceToThis.renderRunning = false;
        }, true);
    this.container.addEventListener("wheel",
        function () {
            // console.log("scroll" + containername);
            referenceToThis.renderRunning = false;
            referenceToThis.startAnimation(referenceToThis)
        }, true);

    // Renderer
    this.renderer = Detector.webgl ? new THREE.WebGLRenderer({ preserveDrawingBuffer: true }) : new THREE.CanvasRenderer();
    //renderer = new THREE.WebGLRenderer( { antialias: true });
    this.renderer.setSize(WIDTH, HEIGHT - 20);
    this.renderer.setClearColor(0xffffff, 1);

    //the statistics widget
    // this.stats.showPanel(1); // 0: fps, 1: ms, 2: mb, 3+: custom
    // this.container.appendChild(this.stats.dom);
}

SurgeryWebGLVisualiser.prototype.pre_init = function () {

    /*
        Signal call
    */
    console.log("pre_init visualisation...");

    // Set up the container and renderer
    var d = document;
    var e = d.documentElement;
    var x = window.innerWidth || e.clientWidth || this.container.clientWidth;
    var y = window.innerHeight || e.clientHeight || this.container.clientHeight;

    var WIDTH = x;
    var HEIGHT = y;

    this.container.appendChild(this.renderer.domElement);

    this.scene = new THREE.Scene();

    // Camera
    this.camera = new THREE.PerspectiveCamera(45, WIDTH / HEIGHT, 0.1, 1000000);
    this.camera.position.set(0, 0, 10);
    this.camera.up = new THREE.Vector3(-1, 0, 0);

    this.scene.add(this.camera);

    // Lighting
    var ambientLight = new THREE.AmbientLight(0x552222);
    ambientLight.intensity = .9;
    this.scene.add(ambientLight);

    var pointLight1 = new THREE.PointLight(0xFFFFFF);
    pointLight1.position.x = 1000000;
    pointLight1.position.y = 10000000;
    pointLight1.position.z = 1300000;
    this.scene.add(pointLight1);

    // Add controls
    this.controls = new THREE.TrackballControls(this.camera, this.container);
    this.controls.target.set(0, 0, 5);
    this.controls.rotateSpeed = 2.0;
    this.controls.zoomSpeed = 1.2;
    this.controls.panSpeed = 0.8;

    this.controls.noZoom = false;
    this.controls.noPan = false;

    this.controls.staticMoving = true;
    this.controls.dynamicDampingFactor = 0.3;

    refThis = this;
    window.onunload = function () {
        refThis.deleteAllSceneRelated();
    }
}

SurgeryWebGLVisualiser.prototype.updateBoundingBox = function (cw, ch, cd) {
    if (cw < this.bBox[0])
        this.bBox[0] = cw;
    else if (cw > this.bBox[3])
        this.bBox[3] = cw;

    if (ch < this.bBox[1])
        this.bBox[1] = ch;
    else if (ch > this.bBox[4])
        this.bBox[4] = ch;

    if (cd < this.bBox[2])
        this.bBox[2] = cd;
    else if (cd > this.bBox[5])
        this.bBox[5] = cd;
}

SurgeryWebGLVisualiser.prototype.resetBoundingBox = function () {
    this.bBox = [Number.MAX_SAFE_INTEGER, Number.MAX_SAFE_INTEGER, Number.MAX_SAFE_INTEGER,
    Number.MIN_SAFE_INTEGER, Number.MIN_SAFE_INTEGER, Number.MIN_SAFE_INTEGER];
}

SurgeryWebGLVisualiser.prototype.makeBoundingBox = function () {
    var width = this.bBox[3] - this.bBox[0];
    var height = this.bBox[4] - this.bBox[1];
    var depth = this.bBox[5] - this.bBox[2];

    /*    
    console.log("makeboundingbox: " + width + " " + height + " " + depth);

    for (var i = 0; i < 6; i++)
        console.log("makeboundingbox: " + this.bBox[i]);
    */
    console.log("bounding box plumbing pieces: " + Math.ceil(width / 6) + " " + Math.ceil(height / 6) + " " + Math.ceil(depth / 6));

    var geometry = new THREE.BoxGeometry(width, height, depth);

    geometry.translate(this.bBox[0] + width / 2 /* 16 * 3*/,
        this.bBox[1] + height / 2,
        this.bBox[2] + depth / 2);

    var cube = new THREE.Mesh(geometry,
        new THREE.MeshBasicMaterial({ wireframe: true, color: 'black' })
    );
    cube.updateMatrix();

    return cube;
}

SurgeryWebGLVisualiser.prototype.mouse3dray = function (x, y) {
    //transform screen coordinates into opengl coordinates
    var mouse3D = new THREE.Vector3((x / this.renderer.domElement.innerWidth) * 2 - 1,
        -(y / this.renderer.domElement.innerHeight) * 2 + 1,
        0.01/*z coordinate is back*/);

    var raycaster = new THREE.Raycaster();
    raycaster.setFromCamera(mouse3D, camera);

    var intersects = raycaster.intersectObjects(this.objectsToClick);

    var found = false;
    if (intersects.length > 0) {
        console.log(intersects[0].point);

        this.scene.remove(lineNotWorking);
        this.notWorkingDefect.vertices = [];

        found = this.findPoint(intersects[0].point, graph2, null);
        if (!found) {
            found = this.findPoint(intersects[0].point, graph, null);
        }

        if (found) {
            this.makeLineSegments(this.makeBuffered(this.notWorkingDefect), this.materialNotWorking);
        }
    }

    return found;
}

/*
  Adds to the scene and returns the last added
*/
SurgeryWebGLVisualiser.prototype.makeLineSegments = function (arrBuffered, material) {
    var lineSegsGenerated = new Array();

    for (var i = 0; i < arrBuffered.length; i++) {
        var lineSegs = new THREE.LineSegments(arrBuffered[i], material);

        // lastLineSeg = lineSegs;
        // this.scene.add(lineSegs);

        lineSegsGenerated.push(lineSegs);
    }

    return lineSegsGenerated;
}

SurgeryWebGLVisualiser.prototype.makeBuffered = function (normalgeom) {
    var retArrays = new Array();

    var chunkLength = normalgeom.vertices.length;
    // console.log("nr vertices:" + chunkLength);

    var remainingVertices = chunkLength;
    var processedVertices = 0;
    if (chunkLength > 4000000) {
        chunkLength = 4000000;
    }

    while (remainingVertices > 0) {
        if (remainingVertices <= chunkLength) {
            chunkLength = remainingVertices;
        }

        var positions = new Float32Array(chunkLength * 3);
        var indices = new Uint32Array(chunkLength);
        for (var i = 0; i < chunkLength; i++) {
            var posInNormalGeom = processedVertices + i;
            positions[i * 3] = normalgeom.vertices[posInNormalGeom].x;
            positions[i * 3 + 1] = normalgeom.vertices[posInNormalGeom].y;
            positions[i * 3 + 2] = normalgeom.vertices[posInNormalGeom].z;
            indices[i] = i;
        }

        var buffGeom = new THREE.BufferGeometry();
        buffGeom.addAttribute('position', new THREE.BufferAttribute(positions, 3));
        buffGeom.setIndex(new THREE.BufferAttribute(indices, 1));

        retArrays.push(buffGeom);

        remainingVertices -= chunkLength;
        processedVertices += chunkLength;
    }

    return retArrays;
}

SurgeryWebGLVisualiser.prototype.checkTime = function () {
    /*either use the standby time 
      or return true when renderRunning is a semaphore*/
    return true;
    //return (renderLastMove + renderStandbyAfter >= Date.now());
}

SurgeryWebGLVisualiser.prototype.startAnimation = function (ref) {
    ref.renderLastMove = Date.now();

    /*daca nu ruleaza inca animatia*/
    if (!ref.renderRunning) {
        //verifica de are voie sa ruleze
        if (ref.checkTime()) {
            ref.renderRunning = true;
            requestAnimationFrame(function () { ref.animate(ref) });
        }
    }
}

SurgeryWebGLVisualiser.prototype.animate = function (ref) {

    // console.log("ref is " + ref);

    ref.renderer.render(ref.scene, ref.camera);

    if (!ref.checkTime() || !ref.renderRunning) {
        ref.renderRunning = false;
    }
    else {
        requestAnimationFrame(function () { ref.animate(ref) });
    }


    ref.controls.update();
}

SurgeryWebGLVisualiser.prototype.makePlumbingPieceBoxes = function (plumb) {
    var totalBounding = new THREE.PalerBoxBufferGeometry(1, 1, 1);
    var totalPrimal = new THREE.PalerBoxBufferGeometry(1, 1, 1);
    var totalDual = new THREE.PalerBoxBufferGeometry(1, 1, 1);

    for (var i = 0; i < plumb.plumbs.length; i++) {
        var boxparam = plumb.plumbs[i].P;

        totalBounding.addBox(boxparam, [1, 1, 1]);

        var ppd = plumb.plumbs[i].D;

        //if(ppd.p[0] == 1)
        var bitPosition = 8;

        if ((ppd.p & bitPosition) == bitPosition) {
            var dim = [0.3, 0.3, 0.3];

            //var b1 = constructBox(boxparam, dim, 'orange', false);
            //totalPrimal.merge(b1);
            totalPrimal.addBox(boxparam, dim);

            for (var j = 1; j < 4; j++) {
                //if(ppd.p[j] == 0)
                bitPosition = 1 << (3 - j);
                if ((ppd.p & bitPosition) == bitPosition) {
                    dim[j - 1] = 0.7;
                    boxparam[j - 1] += 0.3;

                    //var b2 = constructBox(boxparam, dim, 'red', false);
                    //totalPrimal.merge(b2);
                    totalPrimal.addBox(boxparam, dim);

                    dim[j - 1] = 0.3;
                    boxparam[j - 1] -= 0.3;
                }
            }
        }

        //if(ppd.d[0] == 1)
        bitPosition = 8;
        if ((ppd.d & bitPosition) == bitPosition) {
            boxparam[0] += 0.5;
            boxparam[1] += 0.5;
            boxparam[2] += 0.5;

            var dim = [0.3, 0.3, 0.3];
            //var b3 = constructBox(boxparam, dim, 'violet', false);
            //totalDual.merge(b3);
            totalDual.addBox(boxparam, dim);

            for (var j = 1; j < 4; j++) {
                //if(ppd.d[j] == 0)
                bitPosition = 1 << (3 - j);
                if ((ppd.d & bitPosition) == 0)
                    continue;

                dim[j - 1] = 0.7;
                boxparam[j - 1] += 0.3;

                //var b4 = constructBox(boxparam, dim, 'blue', false);
                //totalDual.merge(b4);
                totalDual.addBox(boxparam, dim);

                boxparam[j - 1] -= 0.3;
                dim[j - 1] = 0.3;
            }
        }
    }

    console.log("struct");

    totalBounding.addAttributes();
    totalPrimal.addAttributes();
    totalDual.addAttributes();

    console.log("built");

    return [totalBounding, totalPrimal, totalDual];
}

SurgeryWebGLVisualiser.prototype.start_surgery_view = function (pm_geoms_collection, colors) {

    /*
        Start surgery view
    */

    if (this.scene == null) {
        this.pre_init();
    }
    else {

        for(var lattice_mesh_i = 0; lattice_mesh_i < this.lattice_meshes.length; lattice_mesh_i++)
        {
            this.scene.remove(this.lattice_meshes[lattice_mesh_i]);
            this.lattice_meshes[lattice_mesh_i] = undefined;
        }
        this.lattice_meshes = [];
    }

    for (var color_i = 0; color_i < colors.length; color_i++)
    {
        color = colors[color_i];
        pm_geom_for_color = pm_geoms_collection[color];

        pm_geom_for_color.addAttributes();

        console.log("draw color " + color);

        var buff_geom = new THREE.BufferGeometry();
        buff_geom.addAttribute('position', new THREE.BufferAttribute(pm_geom_for_color.getAttribute('position').array, 3));
        buff_geom.setIndex(new THREE.BufferAttribute(pm_geom_for_color.getIndex().array, 1));
        buff_geom.computeVertexNormals();

        var is_wireframe = false;
        var use_color = color;
        var use_opacity = 0.8;
        if (color == "wireframe")
        {
            is_wireframe = true;
            use_color = "black";
        }
        else if (color == "links")
        {
            is_wireframe = true;
            use_color = "aqua";
        }
        else if (color == "black")
        {
            use_opacity = 1.0;
        }

        var geom_material = new THREE.MeshBasicMaterial({
            wireframe: is_wireframe,
            color: use_color,
            opacity: use_opacity, 
            transparent: use_opacity < 1 ? true : false, 
            side:THREE.DoubleSide
        });

        /*
            Was trying to merge all useless points...Fuck it!
        */

        // var positions = pm_geom_for_color.getAttribute('position');
        // var points = [];
        // for(var pi = 0; pi<positions.length; pi += 3)
        // {
        //     var point = THREE.Vector3();
        //     point.x = positions[pi + 0];
        //     point.y = positions[pi + 1];
        //     point.z = positions[pi + 2];

        //     points.push(point);
        // }
        // var geometry_convex = new THREE.ConvexGeometry( points );

        // var geom_mesh = new THREE.Mesh(geometry_convex, geom_material);

        var geom_mesh = new THREE.Mesh(buff_geom, geom_material);

        /*
            store reference to the 3D object
        */
        this.lattice_meshes.push(geom_mesh);

        this.scene.add(geom_mesh);
    }

    this.animate(this);
}

SurgeryWebGLVisualiser.prototype.makeTextSprite2 = function (message) {
    var canvas = document.createElement('canvas');
    var size = 1024; // CHANGED
    canvas.width = size;
    canvas.height = size;
    var context = canvas.getContext('2d');
    context.fillStyle = '#000000'; // CHANGED
    context.textAlign = 'center';
    context.font = '200px Arial';
    context.fillText(message, size / 2, size / 2);

    var amap = new THREE.Texture(canvas);
    amap.needsUpdate = true;

    var mat = new THREE.SpriteMaterial({
        map: amap,
        transparent: false,
        useScreenCoordinates: false,
        color: 0xffffff // CHANGED
    });

    var sp = new THREE.Sprite(mat);
    sp.scale.set(100, 100, 1); // CHANGED

    return sp;
}

SurgeryWebGLVisualiser.prototype.checkboxClick = function (visOptions) {

    var collectedValues = visOptions.collectValues();

    for (var key in collectedValues) {
        var collVal = collectedValues[key];

        var globjs = [];
        switch (key) {
            case "drawBoxes":
                globjs = [visualisationDefects.boxesGeometry];
                break;
            case "drawPrimals":
                globjs = [visualisationDefects.primalGeometry, visualisationDefects.primalGeometry2];
                break;
            case "drawDuals":
                globjs = [visualisationDefects.dualGeometry, visualisationDefects.dualGeometry2];
                break;
            case "drawUnitsPlumb":
                globjs = [visualisationPlumb.plumbingUnits];
                break;
            case "drawPrimalsPlumb":
                globjs = [visualisationPlumb.plumbingPrimals];
                break;
            case "drawDualsPlumb":
                globjs = [visualisationPlumb.plumbingDuals];
                break;
        }

        for (var i = 0; i < globjs.length; i++) {
            if (collVal.visible) {
                this.scene.add(globjs[i]);
            }
            else {
                this.scene.remove(globjs[i]);
            }
        }
    }

    this.startAnimation(this);
    this.renderRunning = false;
}