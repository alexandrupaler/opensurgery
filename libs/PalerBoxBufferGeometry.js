/**
 * Original from Mugen87 / https://github.com/Mugen87
 * Modified to work with my code
 */

THREE.PalerBoxBufferGeometry = function () {

	THREE.BufferGeometry.call(this);

	this.type = 'PalerBoxBufferGeometry';

	/*
		A maximum limit of the total number of vertices which the geometry can hold
	*/
	// removed two zeros
	var vertexCount = 500000;

	// buffers
	this.vertices = new Float32Array(vertexCount * 3);

	this.indicesCount = 0;
	this.indices = new Uint32Array(vertexCount);

	// a map for the coordinates already used
	// this.existence = new Map();

	// offset variables
	this.vertexBufferOffset = 0;

	// hard coded dimension of this array
	// a face is limited to four corners
	this.corners_3d_points = new Array(4);

	THREE.PalerBoxBufferGeometry.prototype.addBox = function (which_faces, position, dimensions) {

		// // build each side of the box geometry, if specified 
		// if (which_faces == 0)
		// {
		// 	//do not allow for no face to be drawn
		// 	which_faces = 63;
		// }

		if(which_faces == 0)
		{
			return;
		}

		var width = dimensions[0];
		var height = dimensions[1];
		var depth = dimensions[2];

		var poss = {};
		poss['x'] = position[0] ;//+ width / 2;
		poss['y'] = position[1] ;//+ height / 2;
		poss['z'] = position[2] ;//+ depth / 2;

		// build each side of the box geometry
		if((which_faces & 1) == 1)
			this.buildPlane(poss, 'z', 'y', 'x', - 1, - 1, depth, height, width); // px
		if((which_faces & 2) == 2)
			this.buildPlane(poss, 'z', 'y', 'x', 1, - 1, depth, height, - width); // nx
		if((which_faces & 4) == 4)
			this.buildPlane(poss, 'x', 'z', 'y', 1, 1, width, depth, height); // py
		if((which_faces & 8) == 8)
			this.buildPlane(poss, 'x', 'z', 'y', 1, - 1, width, depth, - height); // ny
		if((which_faces & 16) == 16)
			this.buildPlane(poss, 'x', 'y', 'z', 1, - 1, width, height, depth); // pz
		if((which_faces & 32) == 32)
			this.buildPlane(poss, 'x', 'y', 'z', - 1, - 1, width, height, - depth); // nz
	}

	THREE.PalerBoxBufferGeometry.prototype.addAttributes = function () {
		var vertices2 = new Float32Array(this.vertexBufferOffset);

		for (var i = 0; i < this.vertexBufferOffset; i++) {
			vertices2[i] = this.vertices[i];
		}
		//clean ?
		this.vertices = [];

		var indices2 = new Uint32Array(this.indicesCount);
		for (var i = 0; i < this.indicesCount; i++) {
			indices2[i] = this.indices[i];
		}
		//clean ?
		this.indices = [];

		// build geometry
		this.addAttribute('position', new THREE.BufferAttribute(vertices2, 3));
		this.setIndex(new THREE.BufferAttribute(indices2, 1));
	}

	THREE.PalerBoxBufferGeometry.prototype.addVertex = function (vector, vbo) {

		this.vertices[vbo + 0] = vector.x;
		this.vertices[vbo + 1] = vector.y;
		this.vertices[vbo + 2] = vector.z;

		this.indices[this.indicesCount] = this.indicesCount;
		this.indicesCount++;

		vbo += 3;

		return vbo;
	}

	THREE.PalerBoxBufferGeometry.prototype.addFace = function (idx1, idx2, idx3, list) {
		this.vertexBufferOffset = this.addVertex(list[idx1], this.vertexBufferOffset);
		this.vertexBufferOffset = this.addVertex(list[idx2], this.vertexBufferOffset);
		this.vertexBufferOffset = this.addVertex(list[idx3], this.vertexBufferOffset);
	}

	THREE.PalerBoxBufferGeometry.prototype.buildPlane = function (position, u, v, w, udir, vdir, width, height, depth) {

		var segmentWidth = width;
		var segmentHeight = height;

		var widthHalf = width / 2;
		var heightHalf = height / 2;
		var depthHalf = depth / 2;

		var gridX1 = 2;
		var gridY1 = 2;

		for (var iy = 0; iy < gridY1; iy++) {

			var y = iy * segmentHeight - heightHalf;

			for (var ix = 0; ix < gridX1; ix++) {

				var vector = new THREE.Vector3();

				var x = ix * segmentWidth - widthHalf;

				// set values to correct vector component
				vector[u] = x * udir + position[u];
				vector[v] = y * vdir + position[v];
				vector[w] = depthHalf + position[w];

				this.corners_3d_points[iy * gridX1 + ix] = vector;
			}
		}

		for (iy = 0; iy < 1; iy++) {

			for (ix = 0; ix < 1; ix++) {

				// indices
				var a = ix + gridX1 * iy;
				var b = ix + gridX1 * (iy + 1);
				var c = (ix + 1) + gridX1 * (iy + 1);
				var d = (ix + 1) + gridX1 * iy;

				// face one
				this.addFace(a, b, d, this.corners_3d_points);

				//face two
				this.addFace(b, c, d, this.corners_3d_points);
			}
		}
	}
};

THREE.PalerBoxBufferGeometry.prototype = Object.create(THREE.BufferGeometry.prototype);
THREE.PalerBoxBufferGeometry.prototype.constructor = THREE.PalerBoxBufferGeometry;
