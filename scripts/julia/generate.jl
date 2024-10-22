"""
The Julia version of the generate.py, converted using 
- ChatGPT 4o mini
- QWen2-Coder 7B
Modified and reviewed by hand.
"""

# setup the dependencies

using Pkg
Pkg.activate(".")

using JSON
using Glob

mutable struct WoWsGenerate
    _lang_keys::Vector{String}
    _modifiers::Dict{Any,Any}
    _game_info::Dict{String,Dict{String,Any}}

    _params::Dict{Any,Any}
    _params_keys::Vector{String}
    _lang::Dict{Any,Any}
    _lang_sg::Dict{Any,Any}

    WoWsGenerate() = new([], Dict(), Dict("regions" => Dict(), "types" => Dict()),
        Dict(), [], Dict(), Dict())
end

function load_params!(wows::WoWsGenerate)
    """
    Read game params and language files
    """
    println("Reading game params...")
    wows._params = _read_gameparams()
    println("Loaded game params!")
    wows._params_keys = keys(wows._params)
    wows._lang = _read_lang("en")
    # get all Japanese ship names
    wows._lang_sg = _read_lang("zh_sg")
end

#region Helpers
function _read_lang(language::String)::Dict{Any,Any}
    return _read_json("langs/$(language)_lang.json")
end

function _read_supported_langs()
    """
    Read all language files and return a dict
    """
    lang_dict = Dict{String,Any}()
    for lang in _list_dir("langs")
        if occursin(".git", lang)
            continue
        end

        lang = replace(lang, "_lang.json" => "")
        if !(lang in ["en", "ja", "zh_sg", "zh_tw"])
            continue
        end
        println("Reading language $lang...")
        lang_dict[lang] = _read_lang(lang)
    end
    return lang_dict
end

function _read_json(filename::String)::Dict
    json_dict = JSON.parsefile(filename)
    return json_dict
end

function _read_gameparams()
    return JSON.parsefile("GameParams-0.json")
end

function _write_json(data::Dict, filename::String)
    json_str = JSON.json(data)
    open(filename, "w", enc="UTF-8") do f
        write(f, json_str)
    end
end

function _sizeof_json(filename::String)
    """
    Get the size of a json file
    """
    return filesize(filename) / 1024 / 1024
end

function _list_dir(dir::String)::Vector{String}
    """
    List all files in a directory
    """
    return readdir(dir)
end

function round_up(num::Float64, digits::Int=1)::Float64
    return round(num, digits)
end

function _match(text::String, patterns::Vector{String}, method::Function)::Bool
    """
    Match text with patterns
    """
    for pattern in patterns
        if method(text, pattern)
            return true
        end
    end
    return false
end

function _tree(data::Dict, depth::Int=2, tab::Int=0, show_value::Bool=false)
    """
    Show the structure tree of a dict. This is useful when analysing the data.
    """
    if depth == 0
        if show_value
            if isa(data, Dict)
                println("\t"^tab * "- dict")
            else
                println("\t"^tab * "- ", data)
            end
        end
        return
    end

    if !isa(data, Dict)
        if data == ""
            println("\t"^tab, "- empty string")
        else
            println("\t"^tab * "- ", data)
        end
        return
    end

    for (level, value) in data
        println("\t"^tab * "- ", level)
        tree(value, depth - 1, tab + 1, show_value)
    end
end

function _merge(weapons::Vector{Dict})
    """
    join same weapons together into one dict
    """
    merged = []
    counter = []
    for w in keys(weapons)
        if isempty(merged)
            push!(merged, w)
            push!(counter, 1)
            continue
        end

        found = false
        for m in merged
            if w == m
                counter[index(merged, m)] += 1
                found = true
                break
            end
        end
        if !found
            push!(merged, w)
            push!(counter, 1)
        end
    end
    for (i, m) in enumerate(merged)
        m["count"] = counter[i]
    end
    return merged
end

function _IDS(key::String)::String
    return "IDS_" * uppercase(key)
end
#endregion

#region Air Defense
function _unpack_air_defense(ship_module::Dict, params::Dict)
    """
    Unpack air defense info from ship_module and return air_defense dict
    """
    air_defense = Dict()
    near = Vector{Dict}()
    medium = Vector{Dict}()
    far = Vector{Dict}()

    for (aura_key, aura) in ship_module
        if !(isa(aura, Dict) && haskey(aura, "type") && aura["type"] in ["far", "medium", "near"])
            continue
        end

        min_distance = aura["minDistance"] / 1000
        max_distance = aura["maxDistance"] / 1000

        damage = aura["areaDamage"]
        # treat this as the bubble
        if damage == 0
            bubbles = Dict()
            # handle black cloud (bubbles), this deals massive damage
            bubbles["inner"] = Int(aura["innerBubbleCount"])
            bubbles["outer"] = Int(aura["outerBubbleCount"])
            bubbles["rof"] = aura["shotDelay"]
            bubbles["minRange"] = min_distance
            bubbles["maxRange"] = max_distance
            bubbles["hitChance"] = aura["hitChance"]
            bubbles["spawnTime"] = aura["shotTravelTime"]
            # value 7 is from WoWsFT, seems to be a fixed value
            bubbles["damage"] = Int(aura["bubbleDamage"]) * 7
            air_defense["bubbles"] = bubbles
            continue
        end

        # not a bubble, treat this as a normal aa gun
        rate_of_fire = aura["areaDamagePeriod"]
        if damage == 0
            println(aura)
            throw(ArgumentError("Damage should not be 0 if it is not a bubble!"))
        end
        dps = ceil(damage / rate_of_fire)

        # get all AA guns
        aa_guns = aura["guns"]
        aa_guns_info = Vector{Dict}()
        for aa_gun in aa_guns
            gun_dict = Dict()
            gun = ship_module[aa_gun]
            gun_dict["ammo"] = gun["name"]
            gun_dict["each"] = Int(gun["numBarrels"])
            gun_dict["reload"] = Float64(gun["shotDelay"])
            # don't forget about the lang key
            gun_dict["name"] = _IDS(gun["name"])
            push!(wows._lang_keys, gun_dict["name"])
            push!(aa_guns_info, gun_dict)
        end

        air_defense_info = Dict()
        air_defense_info["minRange"] = min_distance
        air_defense_info["maxRange"] = max_distance
        air_defense_info["hitChance"] = aura["hitChance"]
        air_defense_info["damage"] = damage
        air_defense_info["rof"] = round_up(rate_of_fire, 2)
        air_defense_info["dps"] = dps
        air_defense_info["guns"] = _merge(aa_guns_info)

        if occursin("Far", aura_key)
            push!(far, air_defense_info)
        elseif occursin("Med", aura_key)
            push!(medium, air_defense_info)
        elseif occursin("Near", aura_key)
            push!(near, air_defense_info)
        else
            throw(ArgumentError("Unknown air defense type: $aura_key"))
        end
    end

    if !isempty(far)
        air_defense["far"] = far
    end
    if !isempty(medium)
        air_defense["medium"] = medium
    end
    if !isempty(near)
        air_defense["near"] = near
    end
    return air_defense
end
#endregion

#region Guns and Torpedoes
function _unpack_guns_torpedoes(ship_module::Dict)
    """
    Unpack guns and torpedoes
    """
    weapons = []
    # check if
    for weapon_key in keys(ship_module)
        if !occursin("HP", weapon_key)
            continue
        end

        # check each gun / torpedo
        weapon_module = ship_module[weapon_key]
        if !isa(weapon_module, Dict)
            throw(ErrorException("weapon_module is not a dict"))
        end

        current_weapon = Dict()
        current_weapon["reload"] = weapon_module["shotDelay"]
        current_weapon["rotation"] = float(180.0 / weapon_module["rotationSpeed"][1])
        current_weapon["each"] = Int(weapon_module["numBarrels"])
        current_weapon["ammo"] = weapon_module["ammoList"]
        # this is used for ap penetration
        if haskey(weapon_module, "vertSector")
            current_weapon["vertSector"] = weapon_module["vertSector"][2]
        end
        push!(weapons, current_weapon)
    end

    # join same weapons together into one dict
    return _merge(weapons)
end
#endregion

#region Ship Components
function _unpack_ship_components(module_name::String, module_type::String, ship::Dict, params::Dict)
    ship_components = Dict()

    ship_module = ship[module_name]

    if occursin("hull", module_type)
        ship_components["health"] = ship_module["health"]
        flood_nodes = ship_module["floodNodes"]
        flood_probability = flood_nodes[1][1]
        torpedo_protection = 100 - flood_probability * 3 * 100

        if torpedo_protection >= 1
            ship_components["protection"] = round_up(torpedo_protection)
        end

        concealment = Dict()
        visibility = ship_module["visibilityFactor"]
        visibility_plane = ship_module["visibilityFactorByPlane"]
        fire_coeff = ship_module["visibilityCoefFire"]
        fire_coeff_plane = ship_module["visibilityCoefFireByPlane"]
        visibility_submarine = ship_module["visibilityFactorsBySubmarine"]["PERISCOPE"]

        concealment["sea"] = round_up(visibility)
        concealment["plane"] = round_up(visibility_plane)
        concealment["seaInSmoke"] = round_up(ship_module["visibilityCoefGKInSmoke"])
        concealment["planeInSmoke"] = round_up(ship_module["visibilityCoefGKByPlane"])
        concealment["submarine"] = round_up(visibility_submarine)
        concealment["seaFireCoeff"] = fire_coeff
        concealment["planeFireCoeff"] = fire_coeff_plane

        if haskey(ship_module, "SubmarineBattery")
            concealment["coeffSeaUnderwaterDepths"] = ship_module["visibilityCoeffUnderwaterDepths"]
            concealment["coeffPlanUnderwaterDepths"] = ship_module["visibilityCoeffUnderwaterDepths"]
        end

        ship_components["visibility"] = concealment

        mobility = Dict()
        mobility["speed"] = ship_module["maxSpeed"]

        if haskey(ship_module, "SubmarineBattery")
            buoyancy_states = ship_module["buoyancyStates"]
            if haskey(buoyancy_states, "DEEP_WATER_INVUL")
                speed_offset = buoyancy_states["DEEP_WATER_INVUL"][2]
                mobility["speedUnderwater"] = round_up(mobility["speed"] * speed_offset)
            end
        end

        mobility["turningRadius"] = ship_module["turningRadius"]
        mobility["rudderTime"] = round_up(ship_module["rudderTime"] / 1.305)
        ship_components["mobility"] = mobility

        if haskey(ship_module, "SubmarineBattery")
            submarine_battery = Dict()
            submarine_battery["capacity"] = ship_module["SubmarineBattery"]["capacity"]
            submarine_battery["regen"] = ship_module["SubmarineBattery"]["regenRate"]
            ship_components["submarineBattery"] = submarine_battery
        end
    elseif occursin("artillery", module_type)
        artillery = Dict()
        artillery["range"] = ship_module["maxDist"]
        artillery["sigma"] = ship_module["sigmaCount"]
        artillery["guns"] = _unpack_guns_torpedoes(ship_module)

        if haskey(ship_module, "BurstArtilleryModule")
            artillery["burst"] = ship_module["BurstArtilleryModule"]
        end

        ship_components = merge(ship_components, artillery)

        air_defense = _unpack_air_defense(ship_module, params)
        ship_components = merge(ship_components, air_defense)
    elseif occursin("atba", module_type)
        secondaries = Dict()
        secondaries["range"] = ship_module["maxDist"]
        secondaries["sigma"] = ship_module["sigmaCount"]
        secondaries["guns"] = _unpack_guns_torpedoes(ship_module)
        ship_components = merge(ship_components, secondaries)

        air_defense = _unpack_air_defense(ship_module, params)
        ship_components = merge(ship_components, air_defense)
    elseif occursin("torpedoes", module_type)
        torpedo = Dict()
        torpedo["singleShot"] = ship_module["useOneShot"]
        torpedo["launchers"] = _unpack_guns_torpedoes(ship_module)
        ship_components = merge(ship_components, torpedo)
    elseif occursin("airDefense", module_type)
        air_defense = _unpack_air_defense(ship_module, params)
        ship_components = merge(ship_components, air_defense)
    elseif occursin("airSupport", module_type)
        air_support = Dict()
        plane_name = ship_module["planeName"]
        air_support["plane"] = plane_name
        plane_name_title = _IDS(plane_name)
        air_support["name"] = plane_name_title
        push!(wows._lang_keys, plane_name_title)

        air_support["reload"] = ship_module["reloadTime"]
        air_support["range"] = round_up(ship_module["maxDist"] / 1000)
        air_support["chargesNum"] = ship_module["chargesNum"]
        ship_components = merge(ship_components, air_support)
    elseif occursin("depthCharges", module_type)
        depth_charge = Dict()
        depth_charge["reload"] = ship_module["reloadTime"]
        total_bombs = 0

        for (launcher_key, launcher) in ship_module
            if !(isa(launcher, Dict))
                continue
            end

            if total_bombs == 0
                ammo_key = launcher["ammoList"][1]
                depth_charge["ammo"] = ammo_key
            end

            total_bombs += launcher["numBombs"]
        end

        total_bombs *= ship_module["numShots"]
        depth_charge["bombs"] = total_bombs
        depth_charge["groups"] = ship_module["maxPacks"]
        ship_components = merge(ship_components, depth_charge)
    elseif occursin("fireControl", module_type)
        ship_components = ship_module
    elseif occursin("flightControl", module_type)
        # No operation
    elseif module_type in ["torpedoBomber", "diveBomber", "fighter", "skipBomber"]
        ship_components = ship_module["planes"]
    elseif occursin("pinger", module_type)
        pinger = Dict()
        pinger["reload"] = ship_module["waveReloadTime"]
        pinger["range"] = ship_module["waveDistance"]
        sectors = ship_module["sectorParams"]

        if length(sectors) != 2
            throw(ErrorException("pinger has more than 2 sectors"))
        end

        pinger["lifeTime1"] = sectors[1]["lifetime"]
        pinger["lifeTime2"] = sectors[2]["lifetime"]
        pinger["speed"] = ship_module["waveParams"][1]["waveSpeed"][1]
        ship_components = merge(ship_components, pinger)
    elseif occursin("engine", module_type)
        speedCoef = ship_module["speedCoef"]
        if speedCoef != 0
            ship_components["speedCoef"] = speedCoef
        end
    elseif occursin("specials", module_type)
        if haskey(ship_module, "RageMode")
            ship_components["rageMode"] = ship_module["RageMode"]
        end
    elseif occursin("airArmament", module_type)
        # No operation
    elseif occursin("radars", module_type)
        # No operation
    elseif occursin("chargeLasers", module_type)
        # No operation
    elseif occursin("waves", module_type)
        # No operation
    elseif occursin("axisLaser", module_type)
        # No operation
    elseif occursin("abilities", module_type)
        # No operation
    elseif occursin("directors", module_type)
        # No operation
    elseif occursin("finders", module_type)
        # No operation
    elseif occursin("wcs", module_type)
        # No operation
    elseif occursin("shield", module_type)
        # No operation
    elseif occursin("phaserLasers", module_type)
        # No operation
    elseif occursin("photonTorpedoes", module_type)
        # No operation
    else
        throw(ErrorException("Unknown ship_module type: $module_type"))
    end

    return Dict(module_name => ship_components)
end
#endregion

#region Consumables
function _unpack_consumables(abilities_dict::Dict)
    """
    Unpack consumables
    """
    consumables = Vector{Vector{Dict{Symbol,String}}}()
    for (ability_key, ability_slot) in abilities_dict
        abilities = ability_slot[:abils]
        if isempty(abilities)
            continue
        end

        ability_list = Vector{Dict{Symbol,String}}()
        for a in abilities
            push!(ability_list, Dict(:name => a[1], :type => a[2]))
        end
        push!(consumables, ability_list)
    end
    return consumables
end
#endregion

#region Ship Params
function _unpack_ship_params(wows::WoWsGenerate, item::Dict, params::Dict)
    ship_params = Dict()
    ship_index = item["index"]
    ship_id = item["id"]
    lang_key = wows._IDS(ship_index)
    ship_params["name"] = lang_key
    ship_params["description"] = lang_key * "_DESCR"
    ship_params["year"] = lang_key * "_YEAR"
    push!(wows._lang_keys, lang_key)
    push!(wows._lang_keys, lang_key * "_DESCR")
    push!(wows._lang_keys, lang_key * "_YEAR")

    ship_params["paperShip"] = item["isPaperShip"]
    ship_params["id"] = ship_id
    ship_params["index"] = ship_index
    ship_params["tier"] = item["level"]

    nation = item["typeinfo"]["nation"]
    species = item["typeinfo"]["species"]
    wows._game_info["regions"][nation] = true
    wows._game_info["types"][species] = true
    ship_params["region"] = nation
    ship_params["type"] = species
    nation_lang = wows._IDS(nation |> uppercase)
    species_lang = wows._IDS(species |> uppercase)
    ship_params["regionID"] = nation_lang
    ship_params["typeID"] = species_lang
    push!(wows._lang_keys, nation_lang)
    push!(wows._lang_keys, species_lang)

    if length(item["permoflages"]) > 0
        ship_params["permoflages"] = item["permoflages"]
    end
    ship_params["group"] = item["group"]

    consumables = wows._unpack_consumables(item["ShipAbilities"])
    ship_params["consumables"] = consumables

    air_defense = Dict()

    ship_upgrade_info = item["ShipUpgradeInfo"]
    ship_params["costXP"] = ship_upgrade_info["costXP"]
    ship_params["costGold"] = ship_upgrade_info["costGold"]
    ship_params["costCR"] = ship_upgrade_info["costCR"]

    module_tree = Dict()
    component_tree = Dict()
    for module_key in keys(ship_upgrade_info)
        current_module = ship_upgrade_info[module_key]
        if !(current_module isa Dict)
            continue
        end

        if !(haskey(params, module_key))
            throw(ErrorException("$module_key is not in params"))
        end

        cost = Dict()
        module_cost = params[module_key]
        cost["costCR"] = module_cost["costCR"]
        cost["costXP"] = module_cost["costXP"]

        module_info = Dict("cost" => cost)

        module_type = current_module["ucType"]

        module_index = 0
        prev = current_module["prev"]
        while prev != ""
            prev = ship_upgrade_info[prev]["prev"]
            module_index += 1
        end
        module_info["index"] = module_index

        if haskey(current_module, "nextShips")
            next_ship = current_module["nextShips"]
            if length(next_ship) > 0
                if !haskey(ship_params, "nextShips")
                    ship_params["nextShips"] = []
                end
                for s in next_ship
                    if haskey(params, s)
                        push!(ship_params["nextShips"], params[s]["id"])
                    end
                end
            end
        end

        components = current_module["components"]
        module_info["components"] = components

        for component_key in keys(components)
            component_list = components[component_key]
            if length(component_list) == 0
                continue
            end

            for component_name in component_list
                if haskey(component_tree, component_name)
                    continue
                end
                component = wows._unpack_ship_components(component_name, component_key, item, params)

                first_value = first(values(component))
                if length(first_value) == 0
                    continue
                end
                merge!(component_tree, component)
            end
        end

        moduleName = wows._IDS(module_key)
        module_info["name"] = moduleName
        push!(wows._lang_keys, moduleName)
        if haskey(module_tree, module_type)
            push!(module_tree[module_type], module_info)
        else
            module_tree[module_type] = [module_info]
        end
    end
    ship_params["modules"] = module_tree
    ship_params["components"] = component_tree

    if length(air_defense) > 0
        ship_params["airDefense"] = air_defense
    end
    return Dict(ship_id => ship_params)
end
#endregion

#region Achievements
function _unpack_achievements(wows::WoWsGenerate, item::Dict)
    """
    The app will handle icon, achievement name, and description
    """
    achievements = Dict{String,Any}()
    name = uppercase(item["uiName"])
    lang_name = "IDS_ACHIEVEMENT_" * name
    description = "IDS_ACHIEVEMENT_DESCRIPTION_" * name
    achievements["icon"] = name
    achievements["name"] = lang_name
    achievements["description"] = description
    push!(wows._lang_keys, lang_name)
    push!(wows._lang_keys, description)

    achievements["type"] = item["battleTypes"]
    achievements["id"] = item["id"]
    achievements["constants"] = item["constants"]
    return Dict(key => achievements)
end
#endregion

#region Exterior
function _unpack_exteriors(wows::WoWsGenerate, item::Dict, key::String)
    """
    Unpack flags, camouflage and permoflages
    """
    exterior = Dict{String,Any}()
    exterior_type = item["typeinfo"]["species"]
    exterior["type"] = exterior_type

    # NOTE: ENSIGN should never be included in the app due to lots of issues
    if exterior_type == "Ensign"
        return Dict()
    end

    exterior["id"] = item["id"]
    name = wows._IDS(key)
    exterior["name"] = name
    push!(wows._lang_keys, name)
    exterior["icon"] = key

    costCR = item["costCR"]
    if costCR >= 0
        exterior["costCR"] = costCR
    end

    costGold = item["costGold"]
    if costGold >= 0
        exterior["costGold"] = costGold
    end

    # NOTE: this is gone after 0.11.6 update ONLY for camouflages
    if haskey(item, "modifiers") && length(item["modifiers"]) > 0
        exterior["modifiers"] = item["modifiers"]
        # save all the modifiers
        for modifierKey in exterior["modifiers"]
            wows._modifiers[modifierKey] = exterior["modifiers"][modifierKey]
        end
    end

    if exterior_type == "Flags"
        # add the description
        description = name * "_DESCRIPTION"
        exterior["description"] = description
        push!(wows._lang_keys, description)
    end

    return Dict(key => exterior)
end
#endregion

#region Modernization
function _unpack_modernization(wows::WoWsGenerate, item::Dict, params::Dict)
    """
    Unpack ship upgrades
    """
    slot = item["slot"]
    if slot < 0
        return nothing
    end

    name = item["name"]
    lang_name = "IDS_TITLE_" * uppercase(name)
    description = "IDS_DESC_" * uppercase(name)
    push!(wows._lang_keys, lang_name)
    push!(wows._lang_keys, description)

    modernization = Dict{String,Any}()
    modernization["slot"] = slot
    modernization["id"] = item["id"]
    modernization["name"] = lang_name
    modernization["icon"] = name
    modernization["description"] = description
    modernization["costCR"] = item["costCR"]

    tag = item["tags"]
    if length(tag) > 0
        tag = tag[1]
        if tag == "unique"
            modernization["unique"] = true
        elseif tag == "special"
            modernization["special"] = true
        end
    end
    modernization["costCR"] = item["costCR"]
    if length(item["shiplevel"]) > 0
        modernization["level"] = item["shiplevel"]
    end
    if length(item["shiptype"]) > 0
        modernization["type"] = item["shiptype"]
    end
    if length(item["nation"]) > 0
        modernization["nation"] = item["nation"]
    end

    modifiers = item["modifiers"]
    modernization["modifiers"] = modifiers
    # save all the modifiers
    for (key, value) in modifiers
        wows._modifiers[key] = value
    end

    ships = item["ships"]
    ships_id = []
    for ship in ships
        if !haskey(params, ship)
            continue
        end
        push!(ships_id, params[ship]["id"])
    end
    if length(ships_id) > 0
        modernization["ships"] = ships_id
    end

    excludes = item["excludes"]
    excludes_id = []
    for exclude in excludes
        if !haskey(params, exclude)
            continue
        end
        push!(excludes_id, params[exclude]["id"])
    end
    if length(excludes_id) > 0
        modernization["excludes"] = excludes_id
    end
    return Dict(name => modernization)
end
#endregion

#region Weapons deprecated
function _unpack_weapons(item::Dict, key::String)
    """
    Unpack all weapons (anti-air, main battery, secondaries, torpedoes and more)
    """
    # TODO: to be removed because this is included in the ship, not sure if this is needed at all.
    # TODO: to be removed
    weapon = Dict()
    weapon_type = item["typeinfo"]["species"]
    weapon["type"] = weapon_type
    if haskey(item, "ammoList")
        weapon["ammo"] = item["ammoList"]
    end

    if weapon_type == "DCharge"
        # depth charge
    elseif weapon_type == "Torpedo"
        # torpedoes
    elseif weapon_type == "AAircraft"
        # anti-aircraft
    elseif weapon_type == "Main"
        # main battery
    elseif weapon_type == "Secondary"
        # secondaries
    else
        # unknown weapon type
        throw(ErrorException("Unknown weapon type: $weapon_type"))
    end
    return Dict(key => weapon)
end
#endregion

#region Shells
function _unpack_shells(item::Dict{String,Any})::Dict{String,Any}
    """
    Unpack shells, HE & AP shells, HE & AP bombs and more
    """
    projectile = Dict{String,Any}()
    ammo_type = item["ammoType"]
    projectile["ammoType"] = ammo_type
    projectile["speed"] = item["bulletSpeed"]
    projectile["weight"] = item["bulletMass"]

    # HE & SAP penetration value
    pen_cs = item["alphaPiercingCS"]
    if pen_cs > 0
        projectile["penSAP"] = pen_cs
    end
    pen_he = item["alphaPiercingHE"]
    if pen_he > 0
        projectile["penHE"] = pen_he
    end

    projectile["damage"] = item["alphaDamage"]
    burn_chance = item["burnProb"]
    if burn_chance > 0
        # AP and SAP cannot cause fires
        projectile["burnChance"] = burn_chance
    end

    # ricochet angle
    ricochet_angle = item["bulletRicochetAt"]
    if ricochet_angle <= 90
        projectile["ricochetAngle"] = ricochet_angle
        projectile["ricochetAlways"] = item["bulletAlwaysRicochetAt"]
    end

    diameter = item["bulletDiametr"]
    projectile["diameter"] = diameter
    if ammo_type == "AP"
        ap_info = Dict{String,Any}()
        ap_info["diameter"] = diameter
        # get values needed to calculate the penetration of AP
        ap_info["weight"] = item["bulletMass"]
        ap_info["drag"] = item["bulletAirDrag"]
        ap_info["velocity"] = item["bulletSpeed"]
        ap_info["krupp"] = item["bulletKrupp"]
        projectile["ap"] = ap_info
        # caliber is not changing, and overmatch should ignore decimals & no rounding because 8.9 is the same as 8
        overmatch = Int(diameter * 1000 / 14.3)
        projectile["overmatch"] = overmatch
        projectile["fuseTime"] = item["bulletDetonator"]
    end
    return projectile
end
#endregion

#region Projectiles
function _unpack_projectiles(wows::WoWsGenerate, item::Dict, key::String)
    """
    Unpack all projectiles, like shells, torpedoes, and more. This is launched, fired or emitted? from a weapon.
    """
    projectile = Dict{String,Any}()
    projectile_type = item["typeinfo"]["species"]
    projectile["type"] = projectile_type
    projectile_nation = item["typeinfo"]["nation"]
    projectile["nation"] = projectile_nation

    name = wows._IDS(key)
    push!(wows._lang_keys, name)
    projectile["name"] = name

    if projectile_type == "Torpedo"
        projectile["speed"] = item["speed"]
        projectile["visibility"] = item["visibilityFactor"]
        # TODO: divide by 33.3333 to become the real value here or in app?
        projectile["range"] = item["maxDist"]
        projectile["floodChance"] = item["uwCritical"] * 100
        projectile["alphaDamage"] = item["alphaDamage"]
        projectile["damage"] = item["damage"]
        projectile["deepWater"] = item["isDeepWater"]
        # deep water torpedoes cannot hit certain classes of ships
        ignore_classes = item["ignoreClasses"]
        if length(ignore_classes) > 0
            projectile["ignoreClasses"] = ignore_classes
        end
    elseif projectile_type == "Artillery"
        merge!(projectile, wows._unpack_shells(item))
    elseif projectile_type == "Bomb"
        # TODO: need to consider what we want from bomb
        merge!(projectile, wows._unpack_shells(item))
    elseif projectile_type == "SkipBomb"
        # TODO: same as above
        merge!(projectile, wows._unpack_shells(item))
    elseif projectile_type == "Rocket"
        # TODO: same as above
        merge!(projectile, wows._unpack_shells(item))
    elseif projectile_type == "DepthCharge"
        projectile["damage"] = item["alphaDamage"]
        projectile["burnChance"] = item["burnProb"]
        projectile["floodChance"] = item["uwCritical"] * 100
    elseif projectile_type == "Mine"
        # TODO: we don't do this for now
    elseif projectile_type == "Laser"
        # TODO: we don't do this for now
    elseif projectile_type == "PlaneTracer"
        # TODO: we don't do this for now
    elseif projectile_type == "Wave"
        # TODO: we don't do this for now
    elseif projectile_type == "PlaneSeaMine"
        # TODO: we don't do this for now
    elseif projectile_type == "PhotonTorpedo"
        # TODO: we don't do this for now
        # what is this??
    else
        # unknown projectile type
        throw(ErrorException("Unknown projectile type: $projectile_type"))
    end
    return Dict(key => projectile)
end
#endregion

#region Aircrafts
function _unpack_aircrafts(wows::WoWsGenerate, item::Dict, key::String)
    """
    Unpack aircraft, like fighter, bomber, and more.
    """
    aircraft = Dict{String,Any}()
    aircraft_type = item["typeinfo"]["species"]
    aircraft["type"] = aircraft_type
    aircraft["nation"] = item["typeinfo"]["nation"]
    name = wows._IDS(key)
    push!(wows._lang_keys, name)
    aircraft["name"] = name

    if aircraft_type in ["Fighter", "Bomber", "Skip", "Scout", "Dive", "Smoke"]
        hangarSettings = item["hangarSettings"]
        max_aircraft = hangarSettings["maxValue"]
        aircraft["health"] = item["maxHealth"]
        aircraft["totalPlanes"] = item["numPlanesInSquadron"]
        aircraft["visibility"] = item["visibilityFactor"]
        aircraft["speed"] = item["speedMoveWithBomb"]
        if max_aircraft > 0
            # get information for the CV rework
            aircraft_rework = Dict{String,Any}()
            aircraft_rework["restoreTime"] = hangarSettings["timeToRestore"]
            aircraft_rework["maxAircraft"] = max_aircraft

            aircraft_rework["attacker"] = item["attackerSize"]
            aircraft_rework["attackCount"] = item["attackCount"]
            aircraft_rework["cooldown"] = item["attackCooldown"]
            aircraft_rework["minSpeed"] = item["speedMin"]
            aircraft_rework["maxSpeed"] = item["speedMax"]

            # reference from WoWsFT
            boost_time = item["maxForsageAmount"]
            aircraft_rework["boostTime"] = boost_time
            boost_regen = item["forsageRegeneration"]
            # For super carriers, regeneration is 0
            if boost_regen != 0
                aircraft_rework["boostReload"] = boost_time / boost_regen
            end
            aircraft_rework["bombName"] = item["bombName"]

            # get consumables
            consumables = wows._unpack_consumables(item["PlaneAbilities"])
            if length(consumables) > 0
                aircraft_rework["consumables"] = consumables
            end
            aircraft["aircraft"] = aircraft_rework
        end
    elseif aircraft_type == "Airship"
        # TODO: do this if needed
    elseif aircraft_type == "Auxiliary"
        # TODO: not doing this for now
    else
        throw(ErrorException("Unknown aircraft type: $aircraft_type"))
    end
    return Dict(key => aircraft)
end
#endregion

#region Abilities
function _unpack_abilities(wows::WoWsGenerate, item::Dict, key::String)
    """
    Unpack abilities / consumables, like smoke screen, sonar, radar and more.
    """
    abilities = Dict{String,Any}()
    abilities["nation"] = item["typeinfo"]["nation"]

    costCR = item["costCR"]
    if costCR > 0
        abilities["costCR"] = costCR
    end

    costGold = item["costGold"]
    if costGold > 0
        abilities["costGold"] = costGold
    end

    lang_key = uppercase(key)
    name = "IDS_DOCK_CONSUME_TITLE_$lang_key"
    description = "IDS_DOCK_CONSUME_DESCRIPTION_$lang_key"
    abilities["name"] = name
    abilities["id"] = item["id"]
    abilities["description"] = description
    abilities["icon"] = key
    abilities["alter"] = Dict{String,Any}()
    push!(wows._lang_keys, name)
    push!(wows._lang_keys, description)

    ability_dict = Dict{String,Any}()
    for item_key in keys(item)
        ability = item[item_key]
        if !isa(ability, Dict)
            continue
        end

        if item_key == "typeinfo"
            continue
        end

        current_ability = Dict{String,Any}()
        for ability_key in keys(ability)
            value = ability[ability_key]
            if value == nothing || value == ""
                continue
            end
            if ability_key in ["SpecialSoundID", "group"] || occursin("Effect", ability_key)
                continue
            end

            if ability_key == "preparationTime"
                continue
            end

            if ability_key in ["descIDs", "titleIDs"]
                continue
            end

            if ability_key == "iconIDs"
                icon_name = "IDS_DOCK_CONSUME_TITLE_$(uppercase(value))"
                icon_description = "IDS_DOCK_CONSUME_DESCRIPTION_$(uppercase(value))"
                abilities["alter"][value] = Dict("name" => icon_name, "description" => icon_description)
                push!(wows._lang_keys, icon_name)
                push!(wows._lang_keys, icon_description)
            end

            wows._modifiers[ability_key] = value

            if ability_key == "consumableType"
                if !haskey(abilities, "type")
                    ability_type = uppercase(value)
                    abilities["filter"] = ability_type
                    type_lang = "IDS_BATTLEHINT_TYPE_CONSUMABLE_$ability_type"
                    abilities["type"] = type_lang
                    push!(wows._lang_keys, type_lang)
                end
                continue
            end

            if ability_key == "fightersName"
                current_ability[ability_key] = wows._IDS(value)
                continue
            end

            if occursin("_ArtilleryBooster", key) && ability_key == "boostCoeff"
                ability_key = "gmShotDelay"
            end

            current_ability[ability_key] = value
        end

        if length(current_ability) > 0
            ability_dict[item_key] = current_ability
        end
    end

    if isempty(abilities["alter"])
        delete!(abilities, "alter")
    end

    abilities["abilities"] = ability_dict
    return Dict(key => abilities)
end
#endregion

#region Game Maps
function _unpack_game_map(wows)
    """
    Unpack the game map
    """
    game_map = Dict()
    for f in readdir("spaces")
        if isfile("spaces/$(f)/minimap_water.png")
            # valid map
            curr_map = Dict()
            map_name = uppercase(f)
            lang_name = "IDS_SPACES/$(map_name)"
            curr_map["name"] = lang_name
            curr_map["description"] = "$(lang_name)_DESCR"
            game_map[map_name] = curr_map
        end
    end
    return game_map
end
#endregion

#region Commander Skills
function _unpack_commander_skills(wows::WoWsGenerate, item::Dict)
    """
    Unpack the commander skills
    """
    skills = Dict{String,Any}()
    for (key, value) in item
        skills[key] = value
    end
    return skills
end
#endregion

#region Japanese Ship Alias
function _unpack_japanese_alias(item::Dict, lang::Dict)::Dict
    """
    Unpack the japanese ship alias
    """
    ship_id = item["id"]
    ship_index = item["index"]
    return Dict(ship_id => Dict("alias" => lang[_IDS(ship_index)]))
end
#endregion

#region Language
function _unpack_language(wows)
    """
    Get extra strings we need for the app
    """
    return ["IDS_SPECTATE_SWITCH_SHIP", "IDS_MODERNIZATIONS", "IDS_MODULE_TYPE_ABILITIES",
        # units
        "IDS_SECOND", "IDS_KILOMETER", "IDS_KILOGRAMM", "IDS_KNOT", "IDS_METER_SECOND", "IDS_MILLIMETER", "IDS_METER",
        "IDS_UNITS", "IDS_UNITS_SECOND",
        # generic strings
        "IDS_SHIPS", "IDS_BATTLES"]
end
#endregion

#region Convert Game Info
function _convert_game_info()
    """
    Convert game_info from dicts to lists
    """
    regions = wows._game_info["regions"]
    types = wows._game_info["types"]

    wows._game_info["regions"] = collect(keys(regions))
    wows._game_info["types"] = collect(keys(types))
end
#endregion

#region Core Generation
function generate_everything!(wows::WoWsGenerate, game_path::String)
    if isempty(wows._params)
        throw(ErrorException("Call read() first"))
    end

    ships = Dict()
    achievements = Dict()
    exteriors = Dict()
    modernizations = Dict()
    skills = Dict()
    weapons = Dict()
    projectiles = Dict()
    aircrafts = Dict()
    abilities = Dict()
    alias = Dict()
    ship_index = Dict()
    camoboost = Dict()
    dog_tag = Dict()

    for key in _params_keys
        item = _params[key]
        item_type = item["typeinfo"]["type"]
        item_nation = item["typeinfo"]["nation"]
        item_species = item["typeinfo"]["species"]

        if item_species == "Camoboost"
            camoboost[item["id"]] = item
        end

        if item_type == "DogTag"
            dog_tag_index = item["index"]
            dog_tag_id = item["id"]
            dog_tag[dog_tag_id] = Dict("index" => dog_tag_index)
        end

        if item_type == "Ship"
            ships = merge(ships, _unpack_ship_params(wows::WoWsGenerate, item, _params))
            ship_index[item["id"]] = Dict("index" => item["index"], "tier" => item["level"])

            if item["typeinfo"]["nation"] == "Japan"
                alias = merge(alias, _unpack_japanese_alias(item, _lang_sg))
            end
        elseif item_type == "Achievement"
            achievements = merge(achievements, _unpack_achievements(item, key))
        elseif item_type == "Exterior"
            exteriors = merge(exteriors, _unpack_exteriors(item, key))
        elseif item_type == "Modernization"
            modernization = _unpack_modernization(wows::WoWsGenerate, item, _params)
            if nothing(modernization)
                modernizations = merge(modernizations, modernization)
            end
        elseif item_type == "Crew"
            if key == "PAW001_DefaultCrew"
                skills[key] = item
                continue
            end

            if item["CrewPersonality"]["isUnique"] == true
                skills[key] = item
            end

            for s in keys(item["Skills"])
                modifiers = item["Skills"][s]["modifiers"]
                for m in keys(modifiers)
                    _modifiers[m] = modifiers[m]
                end
            end
        elseif item_type == "Gun"
            continue
        elseif item_type == "Projectile"
            projectiles = merge(projectiles, _unpack_projectiles(wows::WoWsGenerate, item, key))
        elseif item_type == "Aircraft"
            aircrafts = merge(aircrafts, _unpack_aircrafts(wows::WoWsGenerate, item, key))
        elseif item_type == "Ability"
            abilities = merge(abilities, _unpack_abilities(wows::WoWsGenerate, item, key))
        end
    end

    if length(ships) == 0
        throw(ErrorException("No ships found. Data is not valid"))
    end

    for camo in keys(camoboost)
        curr = camoboost[camo]
        curr["title"] = _lang_sg[_IDS(curr["name"])]
    end
    println("There are $(length(camoboost)) camoboosts in the game")
    _write_json(camoboost, "camoboost.json")
    println("There are $(length(dog_tag)) dog tags in the game")
    _write_json(dog_tag, "dog_tag.json")

    println("There are $(length(ships)) ships in the game")
    _write_json(ships, "ships.json")
    println("There are $(length(achievements)) achievements in the game")
    _write_json(achievements, "achievements.json")
    println("There are $(length(exteriors)) exteriors in the game")
    _write_json(exteriors, "exteriors.json")
    println("There are $(length(modernizations)) modernizations in the game")
    _write_json(modernizations, "modernizations.json")
    println("There are $(length(weapons)) weapons in the game")
    _write_json(weapons, "weapons.json")
    println("There are $(length(projectiles)) projectiles in the game")
    _write_json(projectiles, "projectiles.json")
    println("There are $(length(aircrafts)) aircrafts in the game")
    _write_json(aircrafts, "aircrafts.json")
    println("There are $(length(abilities)) abilities in the game")
    _write_json(abilities, "abilities.json")
    println("There are $(length(alias)) Japanese alias in the game")
    _write_json(alias, "alias.json")
    println("There are $(length(ship_index)) ship index in the game")
    _write_json(ship_index, "ship_index.json")
    println("We need $(length(_lang_keys)) language keys")
    println("There are $(length(_modifiers)) modifiers in the game")

    modifiers_copy = copy(_modifiers)
    for m in keys(modifiers_copy)
        modifier_name = "IDS_PARAMS_MODIFIER_$(uppercase(m))"
        if !(haskey(_lang_sg, modifier_name))
            modifier_name *= "_DESTROYER"
        end
        if !(haskey(_lang_sg, modifier_name))
            modifier_name = "IDS_$(uppercase(m))"
        end
        if !(haskey(_lang_sg, modifier_name))
            _modifiers["$(m)_name"] = "UNKNOWN!!!"
            continue
        end
        _modifiers["$(m)_name"] = _lang[modifier_name]
    end
    sorted_modifiers = sort(collect(_modifiers))
    _write_json(sorted_modifiers, "modifiers.json")
    println("Save game info")
    _convert_game_info()
    _write_json(_game_info, "game_info.json")

    for key in keys(_lang)
        if _match(key, ["IDS_PARAMS_MODIFIER_", "IDS_MODULE_TYPE_", "IDS_CAROUSEL_APPLIED_", "IDS_SHIP_PARAM_", "IDS_SKILL_", "IDS_DOCK_RAGE_MODE_"], (x, y) -> startswith(x, y))
            push!(_lang_keys, key)
        end
        append!(_lang_keys, _unpack_language(wows))
    end

    lang_file = Dict()
    all_langs = _read_supported_langs()
    all_langs_keys = keys(all_langs)
    for key in all_langs_keys
        lang_file[key] = Dict()
    end

    for key in _lang_keys
        try
            for lang in all_langs_keys
                lang_file[lang][key] = all_langs[lang][key]
            end
        catch e
            println("Missing $(key)")
        end
    end
    _write_json(lang_file, "lang.json")

    commander_skills = _unpack_commander_skills(wows::WoWsGenerate, skills)
    println("There are $(length(commander_skills)) commander skills in the game")
    _write_json(commander_skills, "commander_skills.json")
    skills = commander_skills["PAW001_DefaultCrew"]["Skills"]
    for skill in keys(skills)
        name = split(skill, r"(?=[A-Z])")[2:end]
        name = join(name, "_")
        skills[skill]["name"] = "IDS_SKILL_$(uppercase(name))"
        skills[skill]["description"] = "IDS_SKILL_DESC_$(uppercase(name))"
    end
    println("There are $(length(skills)) skills in the game")
    _write_json(skills, "skills.json")

    total_size = 0
    for json_name in readdir(".")
        if occursin("GameParams", json_name) || occursin("wowsinfo", json_name)
            continue
        end
        total_size += _sizeof_json(json_name)
    end
    println("Total size: $(total_size / 1e6) MB")

    wowsinfo = Dict()
    wowsinfo["ships"] = ships
    wowsinfo["achievements"] = achievements
    wowsinfo["exteriors"] = exteriors
    wowsinfo["modernizations"] = modernizations
    wowsinfo["projectiles"] = projectiles
    wowsinfo["aircrafts"] = aircrafts
    wowsinfo["abilities"] = abilities
    wowsinfo["alias"] = alias
    wowsinfo["skills"] = skills
    wowsinfo["game"] = _game_info

    game_info_path = joinpath(game_path, "game_info.xml")
    open(game_info_path, "r") do f
        game_info = read!(f, String)
        game_version = split(game_info, "installed=\"")[2]
        game_version = split(game_version, "\"")[1]
        public_test = occursin("<id>WOWS.PT.PRODUCTION</id>", game_info)
    end
    wowsinfo["version"] = "$(game_version)$(public_test ? "PT" : "")"

    _write_json(wowsinfo, "wowsinfo.json")
    println("Done")
end
#endregion

#region Main
if abspath(PROGRAM_FILE) == @__FILE__
    if length(ARGS) < 1
        println("Usage: julia generate.jl <path>")
        exit(1)
    end

    path = ARGS[1]
    generate = WoWsGenerate()
    load_params!(generate)
    generate_everything!(generate, path)
end
#endregion
