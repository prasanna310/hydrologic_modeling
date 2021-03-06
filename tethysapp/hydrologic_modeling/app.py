from tethys_sdk.base import TethysAppBase, url_map_maker
from tethys_sdk.stores import PersistentStore


class HydrologicModeling(TethysAppBase):
    """
    Tethys app class for hydrologic modeling.
    """

    name = 'hydrologic modeling'
    index = 'hydrologic_modeling:home'
    icon = 'hydrologic_modeling/images/icon.gif'
    package = 'hydrologic_modeling'
    root_url = 'hydrologic-modeling'
    color = 'blue'
    description = 'Use this app to 1) Prepare a TOPKAPI model, 2) Perform TauDEM terrain analysis, 3) download SSURGO soil dataset, 4) download Daymet Forcing files, or 5) Prepare TOPNET model input files'
    enable_feedback = False
    feedback_emails = []

        
    def url_maps(self):
        """
        Add controllers
        """
        UrlMap = url_map_maker(self.root_url)

        url_maps = (UrlMap(name='home',
                           url='hydrologic-modeling',
                           controller='hydrologic_modeling.controllers.model_input'),

                    UrlMap(name='model_input',
                           url=r'hydrologic-modeling/model_input',
                           controller='hydrologic_modeling.controllers.model_input'),

                    UrlMap(name='model_run',
                           url='hydrologic-modeling/model_run',
                           controller='hydrologic_modeling.controllers.model_run'),

                    # /hydrologic-modeling/model-input2
                    UrlMap(name='model_input2',
                           url='hydrologic-modeling/model_input2',
                           controller='hydrologic_modeling.controllers.model_input2'),


                    UrlMap(name='visualize_shp',
                           url='hydrologic-modeling/visualize_shp',
                           controller='hydrologic_modeling.controllers.visualize_shp'),

                    # # /hydrologic-modeling/test2
                    # UrlMap(name='test2',
                    #        url='hydrologic-modeling/test2',
                    #        controller='hydrologic_modeling.controllers.test2'),



                    UrlMap(name='model_input0',
                           url='hydrologic-modeling/model_input0',
                           controller='hydrologic_modeling.controllers.model_input0'),
                    #
                    # UrlMap(name='test3',
                    #        url='hydrologic-modeling/test3',
                    #        controller='hydrologic_modeling.controllers.test3'),

        )

        return url_maps


    def persistent_stores(self):
        """
        Add one or more persistent stores
        """
        # 'init_stores:init_stream_gage_db' --> format same as abc.xyz:function_name
        stores = (PersistentStore(name='hydrologic_modeling_db',
                                  initializer='hydrologic_modeling.init_stores.init_hydrologic_modeling_db',
                                  spatial=True
                                  ),
                  )

        return stores