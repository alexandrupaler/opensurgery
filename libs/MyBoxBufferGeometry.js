/**
 * @author mrdoob / http://mrdoob.com/
 * @author Mugen87 / https://github.com/Mugen87
 */

// import { Geometry } from '../core/Geometry.js';
// import { BufferGeometry } from '../core/BufferGeometry.js';
// import { Float32BufferAttribute } from '../core/BufferAttribute.js';
// import { Vector3 } from '../math/Vector3.js';

// BoxGeometry

function MyBoxGeometry( width, height, depth, widthSegments, heightSegments, depthSegments ) {

	Geometry.call( this );

	this.type = 'MyBoxGeometry';

	this.parameters = {
		width: width,
		height: height,
		depth: depth,
		widthSegments: widthSegments,
		heightSegments: heightSegments,
		depthSegments: depthSegments
	};

	this.fromBufferGeometry( new MyBoxBufferGeometry( width, height, depth, widthSegments, heightSegments, depthSegments ) );
	this.mergeVertices();

}

MyBoxGeometry.prototype = Object.create( THREE.Geometry.prototype );
MyBoxGeometry.prototype.constructor = MyBoxGeometry;

// BoxBufferGeometry

function MyBoxBufferGeometry( whichfaces, width, height, depth, widthSegments, heightSegments, depthSegments ) {

	THREE.BufferGeometry.call( this );

	this.type = 'MyBoxBufferGeometry';

	this.parameters = {
		width: width,
		height: height,
		depth: depth,
		widthSegments: widthSegments,
		heightSegments: heightSegments,
		depthSegments: depthSegments
	};

	var scope = this;

	width = width || 1;
	height = height || 1;
	depth = depth || 1;

	// segments

	widthSegments = Math.floor( widthSegments ) || 1;
	heightSegments = Math.floor( heightSegments ) || 1;
	depthSegments = Math.floor( depthSegments ) || 1;

	// buffers

	var indices = [];
	var vertices = [];
	var normals = [];
	var uvs = [];

	// helper variables

	var numberOfVertices = 0;
	var groupStart = 0;

	// build each side of the box geometry, if specified 
	if (whichfaces == 0)
	{
		//do not allow for no face to be drawn
		whichfaces = 63;
	}

	if((whichfaces & 1) == 1)
		buildPlane( 'z', 'y', 'x', - 1, - 1, depth, height, width, depthSegments, heightSegments, 0 ); // px
	if((whichfaces & 2) == 2)	
		buildPlane( 'z', 'y', 'x', 1, - 1, depth, height, - width, depthSegments, heightSegments, 1 ); // nx
	if((whichfaces & 4) == 4)
		buildPlane( 'x', 'z', 'y', 1, 1, width, depth, height, widthSegments, depthSegments, 2 ); // py
	if((whichfaces & 8) == 8)
		buildPlane( 'x', 'z', 'y', 1, - 1, width, depth, - height, widthSegments, depthSegments, 3 ); // ny
	if((whichfaces & 16) == 16)
		buildPlane( 'x', 'y', 'z', 1, - 1, width, height, depth, widthSegments, heightSegments, 4 ); // pz
	if((whichfaces & 32) == 32)
		buildPlane( 'x', 'y', 'z', - 1, - 1, width, height, - depth, widthSegments, heightSegments, 5 ); // nz

	// build geometry

	this.setIndex( indices );
	this.addAttribute( 'position', new THREE.Float32BufferAttribute( vertices, 3 ) );
	this.addAttribute( 'normal', new THREE.Float32BufferAttribute( normals, 3 ) );
	this.addAttribute( 'uv', new THREE.Float32BufferAttribute( uvs, 2 ) );

	function buildPlane( u, v, w, udir, vdir, width, height, depth, gridX, gridY, materialIndex ) {

		var segmentWidth = width / gridX;
		var segmentHeight = height / gridY;

		var widthHalf = width / 2;
		var heightHalf = height / 2;
		var depthHalf = depth / 2;

		var gridX1 = gridX + 1;
		var gridY1 = gridY + 1;

		var vertexCounter = 0;
		var groupCount = 0;

		var ix, iy;

		var vector = new THREE.Vector3();

		// generate vertices, normals and uvs

		for ( iy = 0; iy < gridY1; iy ++ ) {

			var y = iy * segmentHeight - heightHalf;

			for ( ix = 0; ix < gridX1; ix ++ ) {

				var x = ix * segmentWidth - widthHalf;

				// set values to correct vector component

				vector[ u ] = x * udir;
				vector[ v ] = y * vdir;
				vector[ w ] = depthHalf;

				// now apply vector to vertex buffer

				vertices.push( vector.x, vector.y, vector.z );

				// set values to correct vector component

				vector[ u ] = 0;
				vector[ v ] = 0;
				vector[ w ] = depth > 0 ? 1 : - 1;

				// now apply vector to normal buffer

				normals.push( vector.x, vector.y, vector.z );

				// uvs

				uvs.push( ix / gridX );
				uvs.push( 1 - ( iy / gridY ) );

				// counters

				vertexCounter += 1;

			}

		}

		// indices

		// 1. you need three indices to draw a single face
		// 2. a single segment consists of two faces
		// 3. so we need to generate six (2*3) indices per segment

		for ( iy = 0; iy < gridY; iy ++ ) {

			for ( ix = 0; ix < gridX; ix ++ ) {

				var a = numberOfVertices + ix + gridX1 * iy;
				var b = numberOfVertices + ix + gridX1 * ( iy + 1 );
				var c = numberOfVertices + ( ix + 1 ) + gridX1 * ( iy + 1 );
				var d = numberOfVertices + ( ix + 1 ) + gridX1 * iy;

				// faces

				indices.push( a, b, d );
				indices.push( b, c, d );

				// increase counter

				groupCount += 6;

			}

		}

		// add a group to the geometry. this will ensure multi material support

		scope.addGroup( groupStart, groupCount, materialIndex );

		// calculate new start value for groups

		groupStart += groupCount;

		// update total number of vertices

		numberOfVertices += vertexCounter;

	}

}

MyBoxBufferGeometry.prototype = Object.create( THREE.BufferGeometry.prototype );
MyBoxBufferGeometry.prototype.constructor = MyBoxBufferGeometry;


// export { MyBoxGeometry, MyBoxBufferGeometry };
