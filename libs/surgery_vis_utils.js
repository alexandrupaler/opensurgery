function check_coordinate_exists(collection, c1, c2, c3)
{
    if (! (c1 in collection))
        return false;
    
    if(! (c2 in collection[c1]) )
        return false;

    if(! (c3 in collection[c1][c2]))
        return false;

    return true;
}

function is_zero_vector(vector)
{
    var ret = true;
    for(var i=0; i<vector.length; i++)
    {
        ret = ret && (vector[i] == 0);
    }

    return ret;
}

function add_coordinates_as_keys(collection, fx, fy, fz)
{
    if(! (fx in collection))
    {
        collection[fx] = {}
    }

    if(! (fy in collection[fx]))
    {
        collection[fx][fy] = {}
    }

    if(! (fz in collection[fx][fy]))
    {
        collection[fx][fy][fz] = -1;
    }
}