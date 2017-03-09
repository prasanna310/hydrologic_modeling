from .model import engine, SessionMaker, Base, model_inputs_table

# this function is called for the first time a db is created, with first_time=True argument
# at this time, this should create all the tables, and if there is initial data, this should create those too
def init_hydrologic_modeling_db(first_time, username='pr'):
    """
    An example persistent store initializer function
    """
    # Create tables
    Base.metadata.create_all(engine)

    # :TODO Initiate the table data
    first_time = True
    if first_time:
        # Make session
        session = SessionMaker()

        # To add value to the db for the first time
        model_run = model_inputs_table(user_name= username,
                                   simulation_name="Sample_Simulation",
                                   simulation_folder="",
                                   simulation_start_date="2015-01-01",
                                   simulation_end_date="2015-02-01",
                                   USGS_gage="10172200",
                                   outlet_y=" 41.74025",
                                   outlet_x="-111.7915",
                                   box_topY="41.85238717312232",
                                   box_bottomY="41.693818807630734",
                                   box_rightX="-111.88729873046873",
                                   box_leftX="-111.66199873046867",
                                   model_engine = "TOPKAPI",
                                   other_model_parameters="X"+"__"+ "1000" + "__"+ "100" + "__"+ "3600"
                                       )
        session.add(model_run)
        session.commit()


        pass
