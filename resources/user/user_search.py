from os import environ
from json import dumps

from flask import request, jsonify
from flask_jwt_extended import fresh_jwt_required, get_jwt_identity
from flask_restful import Resource
from models.user import UserModel
from models.language import LanguageModel
from models.specialty import SpecialtyModel
from requests import codes, get

from schemas.user.user_profile import UserModelSchema
from schemas.specialty import SpecialtySchema

user_model_schema = UserModelSchema()
specialty_model_schema = SpecialtySchema()

class UserSearch(Resource):
    """
    GET
    Takes in identifying params (specialty id, radius, insur ids, sort, lat_long)
    Returns list of specialists matching those parameters
    """

    @fresh_jwt_required
    def get(self, specialty_id: int, radius: int, page: int, sort_by: str):

        # instantiate the current user to be of the UserModel class
        user = UserModel.find_by_uuid(get_jwt_identity())

        if not user.is_verified_professional:
            return {"message": "To protect our users privacy, you must first verify that you are a doctor to use the Icarus Medical Network. Please verify that you are a doctor by contacting support@icarusmed.com."}, 401

        # set all these to false by default so they dont trigger filters in the query
        # if they dont exist in the query string args (below)
        geo = False
        name = False
        language_ids = False
        designation_ids = False
        is_wheelchair_accessible = False
        is_accepting_new_patients = False

        # get query string arguments from the request
        args = request.args

        # if there are query string arguments (user has selected an address or selected advanced search)
        if args:
            # we arent sure if these are coming in
            # so we need to check

            if ('lat' in args) and ('lon' in args):
                lat = args['lat']
                lon = args['lon']
                geo = 'POINT({} {})'.format(lon, lat)
            
            if 'name' in args:
                name = args['name']
            
            if 'language_ids' in args:
                language_ids = args['language_ids'].split(',')
            
            if 'designation_ids' in args:
                designation_ids = args['designation_ids'].split(',')

            # args are coming in as strings, 
            # we need to make sure these values become boolean for query
            if 'is_wheelchair_accessible' in args:
                is_wheelchair_accessible = args['is_wheelchair_accessible'] == "true"

            if 'is_accepting_new_patients' in args:
                is_accepting_new_patients = args['is_accepting_new_patients'] == "true"

        query = user.get_users_within_radius(
                                             searcher_id=user.id,
                                             specialty_id=specialty_id,
                                             radius=radius,
                                             page=page,
                                             sort=sort_by,
                                             u_geo=geo,
                                             name=name,
                                             language_ids=language_ids,
                                             designation_ids=designation_ids,
                                             is_wheelchair_accessible = is_wheelchair_accessible,
                                             is_accepting_new_patients = is_accepting_new_patients,
                                             )
        
        specialists = query.items
        num_specialists = query.total

        # initialize empty array to house all the specialist objects
        specialists_array = []

        # initialize empty array to house all coordinates for the distance calculations
        distance_array = []

        # for each specialist, serialize their information using marshmallow
        # cant send the data in as is because marshmallow cant handle pagination
        # so instead do one usermodel serialization at a time and itll work
        # append the dictionary to the specialists_array
        # results in an array of multiple dictionaries
        for specialist in specialists:

            specialist_dict = user_model_schema.dump(specialist)

            # append to the lists of specialists
            specialists_array.append(specialist_dict)


            for address_row in specialist.provider.addresses:
                # create an array of distances
                distance_array.append('{},{}'.format(
                    address_row.latitude, address_row.longitude))

        destinations = '|'.join(distance_array)

        # # GMAPS BILLING
        # #   num origins * num destinations = num elements.
        # #   billed per num elements
        # #   we get billed for 6 calls here

        # # Distance Matrix calculation
        if geo:
            maps_lat = lat
            maps_lon = lon
        else:
            maps_lat = user.provider.addresses[0].latitude
            maps_lon = user.provider.addresses[0].longitude

        r = get('https://maps.googleapis.com/maps/api/distancematrix/json?units=metric&origins={},{}&destinations={}&key='.format(maps_lat, maps_lon, destinations, environ.get("GOOGLE_MAPS_API_KEY")))

        # # destination matrix to specialists

        # # append the travel distances to the specialists_array if we get a good response from gmaps api
        if r.status_code == codes['ok']:
            json_response = r.json()

            address_loop_count = 0
            for specialist_index in range(len(specialists_array)):
                for specialist_address_index in range((len(specialists_array[specialist_index]['provider']['addresses']))):
                    specialists_array[specialist_index]['provider']['addresses'][specialist_address_index]['distance'] = json_response['rows'][0]['elements'][address_loop_count]['distance']['text']
                    address_loop_count += 1

        # Grab the specialty information to return.
        specialty = SpecialtyModel.find_by_id(specialty_id)

        return {"specialists": specialists_array, "numSpecialists": num_specialists, "specialty": specialty_model_schema.dump(specialty)}, 200
