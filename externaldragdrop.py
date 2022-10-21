import hou
import re
import os
import sys
import platform

if sys.version_info.major < 3:
    from urllib import unquote
else:
    from urllib.parse import unquote
#decode urlpath on windows

def dropAccept(files):
    pane = hou.ui.paneTabUnderCursor() 
    if (pane.type().name() != "NetworkEditor"):
        return False
    hversion = hou.applicationVersion()
    
    for i, file in enumerate(files):
        if (hversion[0] < 18) or (hversion[0] == 18 and hversion[1] == 0):
            
            #print("hversion < 18.5")
            if platform.system() == "Windows":
                file_path = file[8:]
            elif platform.system() == "Linux":
                file_path = file[7:]
        else:
            file_path = file
            #print(file)


        file_path = unquote(file_path) #decode urlpath

        file_basename = os.path.splitext(os.path.basename(file_path))
        file_ext = file_basename[1].lower()

        #convert to relative path
        file_path = rel_path(file_path)
        
        cursor_position = pane.cursorPosition() + hou.Vector2(i *3, 0)

        network_node = pane.pwd()

        #opening hip
        if re.match(".hip", file_ext) != None:
            hou.hipFile.load(file_path)
            return True

        #adding nodes
        try:
            import_file(network_node, file_path, file_basename, file_ext, cursor_position)
        except:
            print(sys.exc_info()[1])
            return False

    return True

def rel_path(fullpath):
    hippath = hou.getenv("HIP")
    if re.match(hippath, fullpath):
        fullpath = "$HIP" +  re.sub(hippath, "", fullpath)
    return fullpath

def import_file(network_node, file_path, file_basename, file_ext, cursor_position):
    #validate node name
    file_name = re.sub(r"[^0-9a-zA-Z\.]+", "_", file_basename[0])
    #create new geo node in obj network if none exists
    if network_node.type().name() == "obj":
        network_node = network_node.createNode("geo", "GEO_" + file_name)
        network_node.setPosition(cursor_position)

    if network_node.type().name() == "geo":
        if file_ext == ".abc":
            create_new_node(network_node, file_path, "alembic", "fileName", cursor_position, name = file_name)
            return True
        elif file_ext == ".rs":
            create_new_node(network_node, file_path, "redshift_packedProxySOP", "RS_proxy_file", cursor_position, name = file_name)
            return True
        elif file_ext == ".ass":
            create_new_node(network_node, file_path, "arnold_asstoc", "ass_file", cursor_position, name = file_name)
            return True
        elif file_ext in {".usd", ".usda", ".usdc"}:
            create_new_node(network_node, file_path, "usdimport", "filepath1", cursor_position, name = file_name)
        else:
            create_new_node(network_node, file_path, "file", "file", cursor_position, name = file_name)
            return True
    elif network_node.type().name() in {"mat","materialbuilder", "materiallibrary"}:
        create_new_node(network_node, file_path, "texture::2.0", "map", cursor_position, name = file_name)
        return True


    elif network_node.type().name() == "redshift_vopnet":
        inner=network_node.node('StandardMaterial1')
        out=network_node.node('redshift_material1')
        if "BaseColor" in file_path:
            albedo = network_node.createNode("redshift::TextureSampler", "BaseColor")
            albedo.setPosition(cursor_position)
            albedo.parm('tex0').set(file_path)
            inner.setInput(0,albedo)
        elif "Diffuse" in file_path:
            albedo = network_node.createNode("redshift::TextureSampler", "BaseColor")
            albedo.setPosition(cursor_position)
            albedo.parm('tex0').set(file_path)
            inner.setInput(0,albedo)
        elif "Albedo" in file_path:
            albedo = network_node.createNode("redshift::TextureSampler", "BaseColor")
            albedo.setPosition(cursor_position)
            albedo.parm('tex0').set(file_path)
            inner.setInput(0,albedo)

        elif "Metal" in file_path:
            metal = network_node.createNode("redshift::TextureSampler", "Metal")
            metal.setPosition(cursor_position)
            metal.parm('tex0').set(file_path)
            metal.parm('tex0_colorSpace').set('raw')
            inner.setInput(3,metal)

        elif "Rough" in file_path:
            Rough = network_node.createNode("redshift::TextureSampler", "Roughness")
            Rough.setPosition(cursor_position)
            Rough.parm('tex0').set(file_path)
            Rough.parm('tex0_colorSpace').set('raw')
            inner.setInput(6,Rough)

        elif "Normal" in file_path:
            Normal = network_node.createNode("redshift::TextureSampler", "Normal")
            bump=network_node.createNode('BumpMap')
            Normal.setPosition(cursor_position)
            bump.parm('scale').set(0.1)
            bump.parm('inputType').set('Tangent-Space Normal')
            Normal.parm('tex0').set(file_path)
            Normal.parm('tex0_colorSpace').set('Raw')
            bump.setInput(0,Normal)
            out.setInput(2,bump)

        elif "Displace" in file_path:
            Displace = network_node.createNode("redshift::TextureSampler", "dis")
            dis=network_node.createNode('redshift::Displacement')
            Displace.setPosition(cursor_position)
            Displace.parm('tex0').set(file_path)
            Displace.parm('tex0_colorSpace').set('raw')
            dis.setInput(0,Displace)
            out.setInput(1,dis)
        


    elif network_node.type().name() == "chopnet":
        create_new_node(network_node, file_path, "file", "file", cursor_position, name = file_name)
        return True


# ARNODLD
    elif network_node.type().name() in {"arnold_materialbuilder", "arnold_vopnet"}:
        inner=network_node.node('standard_surface1')
        out=network_node.node('OUT_material')

        if "BaseColor" in file_path:
            albedo = network_node.createNode("arnold::image", "BaseColor")
            albedo.setPosition(cursor_position)
            albedo.parm('filename').set(file_path)
            inner.setInput(1,albedo)
        elif "Diffuse" in file_path:
            albedo = network_node.createNode("arnold::image", "BaseColor")
            albedo.setPosition(cursor_position)
            albedo.parm('filename').set(file_path)
            inner.setInput(1,albedo)
        elif "Albedo" in file_path:
            albedo = network_node.createNode("arnold::image", "BaseColor")
            albedo.setPosition(cursor_position)
            albedo.parm('filename').set(file_path)
            inner.setInput(1,albedo)

        elif "Metal" in file_path:
            metal = network_node.createNode("arnold::image", "Metal")
            metal.setPosition(cursor_position)
            metal.parm('filename').set(file_path)
            inner.setInput(3,metal)

        elif "Rough" in file_path:
            Rough = network_node.createNode("arnold::image", "Roughness")
            Rough.setPosition(cursor_position)
            Rough.parm('filename').set(file_path)
            inner.setInput(6,Rough)

        elif "Normal" in file_path:
            Normal = network_node.createNode("arnold::image", "Normal")
            bump=network_node.createNode('arnold::bump2d','bump')
            Normal.setPosition(cursor_position)
            bump.parm('bump_height').set(0.1)
            Normal.parm('filename').set(file_path)
            bump.setInput(0,Normal)
            inner.setInput(39,bump)

        elif "Displace" in file_path:
            Displace = network_node.createNode("arnold::image", "dis")
            dis=network_node.createNode('arnold::bump3d','displace')
            Displace.setPosition(cursor_position)
            Displace.parm('filename').set(file_path)
            dis.parm('bump_height').set(0.1)
            dis.setInput(0,Displace)
            out.setInput(1,dis)
 
    elif network_node.type().name() == "subnet":
        inner=network_node.node('mtlxstandard_surface1')
        out=network_node.node('surface_output')
        out2=network_node.node('displacement_output')

        if "BaseColor" in file_path:
            albedo = network_node.createNode("mtlximage", "BaseColor")
            albedo.setPosition(cursor_position)
            albedo.parm('file').set(file_path)
            inner.setInput(1,albedo)
        elif "Diffuse" in file_path:
            albedo = network_node.createNode("mtlximage", "BaseColor")
            albedo.setPosition(cursor_position)
            albedo.parm('file').set(file_path)
            inner.setInput(1,albedo)
        elif "Albedo" in file_path:
            albedo = network_node.createNode("mtlximage", "BaseColor")
            albedo.setPosition(cursor_position)
            albedo.parm('file').set(file_path)
            inner.setInput(1,albedo)

        elif "Metal" in file_path:
            metal = network_node.createNode("mtlximage", "Metal")
            metal.setPosition(cursor_position)
            metal.parm('signature').set('Float')
            metal.parm('file').set(file_path)
            inner.setInput(3,metal)

        elif "Rough" in file_path:
            Rough = network_node.createNode("mtlximage", "Roughness")
            Rough.setPosition(cursor_position)
            Rough.parm('signature').set('Float')
            Rough.parm('file').set(file_path)
            inner.setInput(6,Rough)

        elif "Normal" in file_path:
            Normal = network_node.createNode("mtlximage", "Normal")
            bump=network_node.createNode('mtlxnormalmap','normal_map')
            Normal.setPosition(cursor_position)
            bump.parm('scale').set(0.1)
            Normal.parm('file').set(file_path)
            bump.setInput(0,Normal)
            inner.setInput(40,bump)

        elif "Displace" in file_path:
            Displace = network_node.createNode("mtlximage", "dis")
            dis=network_node.createNode('mtlxdisplacement','displace')
            Displace.setPosition(cursor_position)
            Displace.parm('signature').set('Float')
            Displace.parm('file').set(file_path)
            dis.parm('scale').set(0.1)
            dis.setInput(0,Displace)
            out2.setInput(0,dis)



    elif network_node.type().name() in {"cop2net", "img"}:
        create_new_node(network_node, file_path, "file", "filename1", cursor_position, name = file_name)
        return True
    elif network_node.type().name() in {"lopnet","stage"}:
        create_new_node(network_node, file_path, "reference", "filepath1", cursor_position, name = file_name)
        return True
    return False

def create_new_node(network_node, file_path, node_name, parm_path_name, cursor_position, **kwargs):
    name =  kwargs.get('name', None)
    if name:
        new_node = network_node.createNode(node_name, name)
    else:
        new_node = network_node.createNode(node_name)
    new_node.setPosition(cursor_position)
    new_node.setParms({parm_path_name:file_path})


    return new_node
