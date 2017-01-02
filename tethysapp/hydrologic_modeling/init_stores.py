from .model import engine, SessionMaker, Base, model_inputs_table

# this function is called for the first time a db is created, with first_time=True argument
# at this time, this should create all the tables, and if there is initial data, this should create those too
def init_hydrologic_modeling_db(first_time):
    """
    An example persistent store initializer function
    """
    # Create tables
    Base.metadata.create_all(engine)

    # :TODO Initiate the table data
    if first_time:
        # Make session
        # session = SessionMaker()
        #
        # # To add value to the db for the first time
        # model_run = model_inputs_table(user_name= "",
        #                            simulation_name="Sample_Simulation",
        #                            simulation_folder="",
        #                            simulation_start_date="",
        #                            simulation_end_date="",
        #                            USGS_gage="",
        #                             outlet_lat="",
        #                            outlet_lon="",
        #                            box_topY="",
        #                            box_bottomY="",
        #                            box_rightX="",
        #                            box_leftX="",
        #                            other_model_parameters="")
        # session.add(model_run)
        # session.commit()


        pass
