import os
import sqlite3
import numpy as np
import pandas as pd
from glob import glob
import datetime

sqlite3.register_adapter(np.int64, lambda x: int(x))
sqlite3.register_adapter(np.int32, lambda x: int(x))

PATH_DB = 'src/data/landlord.sqlite'    
PATH_TO_LOAD = 'data/to_load_landlord/'
PATH_LOADED = 'data/to_load_landlord/loaded_landlord/'


FILE_PATTERN_reviews = 'reviews*.csv'
FILE_PATTERN_properties = 'properties*.csv'


FILE_PATTERN_states = 'states*.csv'
FILE_PATTERN_zips = 'zips*.csv'


## BaseDB class from Professor Ron Smith, DATA 302 – Databases ##
class BaseDB:
    
    def __init__(self, 
                 path_db: str,
                 create: bool = False
                ):

        # Internal flag to indicate if we are connected to the database
        self._connected = False

        # Normalize path format (e.g., windows vs. mac/linux)
        self.path = os.path.normpath(path_db)

        # Check if the database exists, then either create it
        # or throw an error if create=False
        self._check_exists(create)
        return
        
    def run_query(self,
                  sql: str,
                  params: dict = None,
                  keep_open: bool = False
                 ) -> pd.DataFrame:

        # Make sure we have an active connection
        self._connect()

        try:
            # Run the query
            results = pd.read_sql(sql, self._conn, params=params)
        except Exception as e:
            raise type(e)(f'sql: {sql}\nparams: {params}') from e
            print(e)
        finally:
            if not keep_open:
                self._close()
        
        return results

    def run_action(self,
                   sql: str,
                   params: dict = None,
                   keep_open: bool = False
                  ) -> int:

        # Make sure we have an active connection
        self._connect()
    
        try:
            if params is not None:
                self._curs.execute(sql, params)
            else:
                self._curs.execute(sql)
        except Exception as e:
            self._conn.rollback()
            self._close()
            print(e)
            raise type(e)(f'sql: {sql}\nparams: {params}') from e
        finally:
            if not keep_open:
                self._close()
        
        return self._curs.lastrowid
        
    def _check_exists(self, create: bool) -> None:
        '''
        Check if the database file (and all directories in the path)
        exist. If not create them if create=True, or raise an error
        if create=False.
        
        If database did not exist, set self._existed=False, otherwise
        set self._existed=True.
        '''

        self._existed = True

        # Split the path into individial directories, etc.
        path_parts = self.path.split(os.sep)

        # Starting in the current directory,
        # check if each subdirectory, and finally the database file, exist
        n = len(path_parts)
        for i in range(n):
            part = os.sep.join(path_parts[:i+1])
            if not os.path.exists(part):
                self._existed = False
                if not create:
                    raise FileNotFoundError(f'{part} does not exist.')
                if i == n-1:
                    print('Creating db')
                    self._connect()
                    self._close()
                else:
                    os.mkdir(part)
        return

    def _connect(self) -> None:
        if not self._connected:
            self._conn = sqlite3.connect(self.path)
            self._curs = self._conn.cursor()
            self._curs.execute("PRAGMA foreign_keys=ON;")
            self._connected = True
        return

    def _close(self) -> None:
        self._conn.close()
        self._connected = False
        return

class Landlord_DB(BaseDB):
    def __init__(self, 
                 create: bool = True
                ):
        # Call the constructor for the parent class
        super().__init__(PATH_DB, create)

        # If the database did not exist, we need to create it
        if not self._existed:
            print('creating tables')
            self._create_tables()
        return

    def _create_tables(self) -> None:
        """
        Creates Tables
        """


        sql = """
            CREATE TABLE tOwner (
                owner_id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT UNIQUE,
                company_name_display TEXT,
                ind_name TEXT,
                ind_name_display TEXT,
                company_address TEXT
        )
        ;"""
        self.run_action(sql)
        
        sql = """
            CREATE TABLE tProperty (
                pid INT PRIMARY KEY,
                owner_id INTEGER NOT NULL REFERENCES tOwner(owner_id),
                address TEXT NOT NULL UNIQUE,
                address_display TEXT NOT NULL,
                total_value INT,
                rental_units INT,
                usage TEXT,
                bedrooms INT,
                half_baths INT,
                full_baths INT,
                image_path TEXT
            )
            ;"""
        self.run_action(sql)
        
        sql = """
            CREATE TABLE tResponse (
                resp_id INTEGER PRIMARY KEY AUTOINCREMENT,
                pid INTEGER NOT NULL REFERENCES tProperty(pid),
                resp_date TEXT,
                property_rating INT,
                property_review TEXT,
                landlord_name TEXT NOT NULL,
                landlord_rating INT,
                landlord_review TEXT,
                total_rent TEXT,
                ind_rent TEXT,
                utilities TEXT,
                parking TEXT
            )
            ;"""
        self.run_action(sql)
        return


#########################################################################################################
    def load_owner_file(self, file_path: str) -> None:
        """
        Load owner data into the database. (Only should be called once when setting up database)
        """
        df = pd.read_csv(
            file_path,
            dtype={
                'company_name': str,
                'company_name_display': str,
                'ind_name': str,
                'ind_name_display': str,
                'company_address': str
            }
        )
        print('Owner File Loading')
        for row in df.to_dict(orient='records'):
            owner_id = self.get_owner_id(
                row['company_name'],
                row['company_name_display'],
                row['ind_name'],
                row['ind_name_display'],
                row['company_address']
            )
        self._conn.commit()
        self._close()
        return

    def load_property_file(self, file_path: str) -> None:
        """
        Load property data into the database. (Only should be called once when setting up database)
        """
        df = pd.read_csv(
            file_path,
            dtype={
                'pid': int,
                'company_name': str,
                'address': str,
                'address_display': str,
                'total_value': int,
                'rental_units': int,
                'usage': str,
                'bedrooms': int,
                'half_baths': int,
                'full_baths': int,
                'image_path': str
            }
        )
        print('Property File Loading')
        for row in df.to_dict(orient='records'):
            owner_id = self.get_owner_id(
                row['company_name'],
                None,
                None,
                None,
                None
            )
            property_id = self.get_property_id(
                row['pid'],
                owner_id,
                row['address'],
                row['address_display'],
                row['total_value'],
                row['rental_units'],
                row['usage'],
                row['bedrooms'],
                row['half_baths'],
                row['full_baths'],
                row['image_path']
            )
        self._conn.commit()
        self._close()
        return

    def load_response_file(self, file_path: str) -> None:
        """
        Load a landlords_responses*.csv into the database,
        using pid directly (no address lookup) and including resp_date.
        """
        df = pd.read_csv(
            file_path,
            dtype={
                'pid': int,
                'resp_date': str,
                'property_rating': 'Int64',
                'property_review': str,
                'landlord_name': str,
                'landlord_rating': 'Int64',
                'landlord_review': str,
                'total_rent': str,
                'ind_rent': str,
                'utilities': str,
                'parking': str
            }
        )

        print('Response File Loading')
        for row in df.to_dict(orient='records'):
            self.set_response(
                pid=row['pid'],
                resp_date=row['resp_date'],
                property_rating=row['property_rating'],
                property_review=row['property_review'],
                landlord_name=row['landlord_name'],
                landlord_rating=row['landlord_rating'],
                landlord_review=row['landlord_review'],
                total_rent=row['total_rent'],
                ind_rent=row['ind_rent'],
                utilities=row['utilities'],
                parking=row['parking']
            )

        self._conn.commit()
        self._close()
        return
################################################################################
    
    def get_owner_id(self,
                     company_name: str,
                     company_name_display: str = None,
                     ind_name: str = None,
                     ind_name_display: str = None,
                     company_address: str = None) -> int:
        """
        Get (and create if needed) an owner_id.
        """
        sql_select = """
            SELECT owner_id
            FROM tOwner
            WHERE company_name = :company_name
        ;"""
        sql_insert = """
            INSERT INTO tOwner (
                company_name,
                company_name_display,
                ind_name,
                ind_name_display,
                company_address
            ) VALUES (
                :company_name,
                :company_name_display,
                :ind_name,
                :ind_name_display,
                :company_address
            )
        ;"""
        params = {
            'company_name': company_name,
            'company_name_display': company_name_display,
            'ind_name': ind_name,
            'ind_name_display': ind_name_display,
            'company_address': company_address
        }

        query = self.run_query(sql_select, params, keep_open=True)
        if len(query) == 0:
            owner_id = self.run_action(sql_insert, params, keep_open=True)
        else:
            owner_id = int(query.iloc[0]['owner_id'])
        return owner_id
    
    
    def get_property_id(self, 
                        pid: int, 
                        owner_id: int, 
                        address: str, 
                        address_display: str,
                        total_value: int = None, 
                        rental_units: int = None, 
                        usage: str = None, 
                        bedrooms: int = None, 
                        half_baths: int = None, 
                        full_baths: int = None, 
                        image_path: str = None) -> int:
            """
            Get (and create if needed) a property by its pid.
            """
            sql_select = """
                SELECT pid
                FROM tProperty
                WHERE pid = :pid
            ;"""
            sql_insert = """
                INSERT INTO tProperty (
                    pid,
                    owner_id,
                    address,
                    address_display,
                    total_value,
                    rental_units,
                    usage,
                    bedrooms,
                    half_baths,
                    full_baths,
                    image_path
                ) VALUES (
                    :pid,
                    :owner_id,
                    :address,
                    :address_display,
                    :total_value,
                    :rental_units,
                    :usage,
                    :bedrooms,
                    :half_baths,
                    :full_baths,
                    :image_path
                )
            ;"""
            params = {
                'pid': pid,
                'owner_id': owner_id,
                'address': address,
                'address_display': address_display,
                'total_value': total_value,
                'rental_units': rental_units,
                'usage': usage,
                'bedrooms': bedrooms,
                'half_baths': half_baths,
                'full_baths': full_baths,
                'image_path': image_path
            }
            
            query = self.run_query(sql_select, params, keep_open=True)
            if len(query) == 0:
                prop_id = self.run_action(sql_insert, params, keep_open=True)
            else:
                prop_id = int(query.iloc[0]['pid'])
            return prop_id
    
    
    def get_property_by_address(self,
                                address: str
                               ) -> dict:
        """
        Fetch a property row by its address;
        returns a dict or raises if not found.
        """
        sql = """
            SELECT *
            FROM tProperty
            WHERE address = :address
        ;"""
        params = {'address': address}

        df = self.run_query(sql, params, keep_open=True)
        if df.empty:
            raise KeyError(f"No property found with address '{address}'")
        return df.iloc[0].to_dict()


    def set_response(self,
                     pid: int,
                     resp_date: str,
                     property_rating: int = None,
                     property_review: str = None,
                     landlord_name: str = None,
                     landlord_rating: int = None,
                     landlord_review: str = None,
                     total_rent: str = None,
                     ind_rent: str = None,
                     utilities: str = None,
                     parking: str = None
                    ) -> int:
        """
        Insert a response into tResponse if not duplicate;
        returns resp_id.
        """
        sql_select = """
            SELECT resp_id
              FROM tResponse
             WHERE pid           = :pid
               AND resp_date     = :resp_date
               AND landlord_name = :landlord_name
               AND total_rent    = :total_rent
        ;"""
        sql_insert = """
            INSERT INTO tResponse (
                pid,
                resp_date,
                property_rating,
                property_review,
                landlord_name,
                landlord_rating,
                landlord_review,
                total_rent,
                ind_rent,
                utilities,
                parking
            ) VALUES (
                :pid,
                :resp_date,
                :property_rating,
                :property_review,
                :landlord_name,
                :landlord_rating,
                :landlord_review,
                :total_rent,
                :ind_rent,
                :utilities,
                :parking
            )
        ;"""
        params = {
            'pid':pid,
            'resp_date':resp_date,
            'property_rating':property_rating,
            'property_review':property_review,
            'landlord_name':landlord_name,
            'landlord_rating':landlord_rating,
            'landlord_review':landlord_review,
            'total_rent':total_rent,
            'ind_rent':ind_rent,
            'utilities':utilities,
            'parking':parking
        }

        df = self.run_query(sql_select, params, keep_open=True)
        if df.empty:
            resp_id = self.run_action(sql_insert, params, keep_open=True)
        else:
            resp_id = int(df.iloc[0]['resp_id'])
        return resp_id

################################################################################
    
    def get_address_list(self):
        sql = """ 
            SELECT DISTINCT address_display
            FROM tProperty
            ;"""
        return self.run_query(sql)['address_display'].to_list() 
        
    def get_pid_from_address_display(self, add_for_pid):
        sql = """
            SELECT pid
            FROM tProperty 
            WHERE(address_display == :add_for_pid)
        ;"""
        return self.run_query(sql, params={'add_for_pid':add_for_pid})['pid'][0]

    
    def get_property_image(self, pid):
        sql = """
            SELECT image_path
            FROM tProperty 
            JOIN tOwner USING(owner_id)
            WHERE(pid == :pid_input)
            ;"""
        return self.run_query(sql, params={'pid_input':pid})['image_path'][0]

    def get_property_details(self, pid):
        sql = """
        SELECT ind_name_display, bedrooms, half_baths, full_baths, rental_units
        FROM tProperty 
        JOIN tOwner USING(owner_id)
        WHERE(pid == :pid_input)
        ;"""
        return self.run_query(sql, params={'pid_input':pid}).loc[0].to_list()

    def get_avg_landlord_rating(self, pid):
        sql = """
            WITH FindOwner as (
                SELECT ind_name
                FROM tProperty 
                JOIN tOwner USING(owner_id)
                WHERE(pid == :pid_input)
                )
                
            SELECT address, owner_id, ind_name, 1.0*sum(landlord_rating)/count(landlord_rating) as average_landlord_rating, count(landlord_rating) as num_landlord_rating
            FROM tResponse
            JOIN tProperty USING(pid)
            JOIN tOwner USING(owner_id)
            WHERE (ind_name = (SELECT ind_name FROM FindOwner))
            GROUP BY ind_name
            ;"""
        
        output = self.run_query(sql, params={'pid_input':pid})[['average_landlord_rating', 'num_landlord_rating']]
        if len(output['num_landlord_rating']) == 0:
            return 'No Ratings'
        else:
            return output.iloc[0].to_list()

    def get_avg_property_rating(self, pid):
        sql = """
            SELECT 1.0*sum(property_rating)/count(property_rating) as average_property_rating, count(property_rating) as num_property_rating
            FROM tResponse
            JOIN tProperty USING(pid)
            WHERE (pid = :pid_input)
        ;"""
        output = self.run_query(sql, params={'pid_input':pid})[['average_property_rating', 'num_property_rating']]
        if output.loc[0, 'num_property_rating'] == 0:
            return 'No Ratings'
        else:
            return output.iloc[0].to_list()

    def get_modal_data(self, pid):
        sql = """
        SELECT  total_rent, count(total_rent)
        FROM tResponse
        WHERE pid == :pid
        GROUP BY total_rent
        ORDER BY count(total_rent) DESC
        LIMIT 1
        ;"""
        total_rent = self.run_query(sql, params={'pid':pid})['total_rent']
        
        sql = """
                SELECT  ind_rent, count(ind_rent)
                FROM tResponse
                WHERE pid == :pid
                GROUP BY ind_rent
                ORDER BY count(ind_rent) DESC
                LIMIT 1
                ;"""
        ind_rent = self.run_query(sql, params={'pid':pid})['ind_rent']
        
        sql = """
                SELECT  utilities, count(utilities)
                FROM tResponse
                WHERE pid == :pid
                GROUP BY ind_rent
                ORDER BY count(utilities) DESC
                LIMIT 1
                ;"""
        utilities = self.run_query(sql, params={'pid':pid})['utilities']
        
        sql = """
                SELECT  parking, count(parking)
                FROM tResponse
                WHERE pid == :pid
                GROUP BY parking
                ORDER BY count(parking) DESC
                LIMIT 1
                ;"""
        parking = self.run_query(sql, params={'pid':pid})['parking']
        
        return total_rent.to_list(), ind_rent.to_list(), utilities.to_list(), parking.to_list()
    
    def get_recent_reviews(self, pid):
        sql = """
                SELECT property_review	 
                FROM tResponse
                WHERE (pid=:pid) AND (property_review IS NOT NULL)
                ORDER BY resp_id DESC
                LIMIT 1
            ;"""
        property_review = self.run_query(sql, params={'pid':pid})
        if len(property_review['property_review'])==0: 
            property_review = 'No Reviews'
        else:
            property_review = property_review['property_review'].to_list()[0]

        sql = """
            WITH FindOwner as (
                    SELECT ind_name
                    FROM tProperty 
                    JOIN tOwner USING(owner_id)
                    WHERE(pid == :pid_input)
                    )
        
              SELECT landlord_review--, pid, owner_id, ind_name, resp_id
              FROM tResponse
              JOIN tProperty USING(pid)
              JOIN tOwner USING(owner_id)
              WHERE (landlord_review IS NOT NULL) AND (ind_name = (SELECT ind_name FROM FindOwner))
              ORDER BY resp_id DESC
              LIMIT 1
        ;"""
        landlord_review = self.run_query(sql, params = {'pid_input':pid})
        if len(landlord_review['landlord_review'])==0: 
            landlord_review = 'No Reviews'
        else:
            landlord_review = landlord_review['landlord_review'].to_list()[0]

        return property_review, landlord_review

    def insert_response(self, address, 
                        property_rating, 
                        property_review,
                        landlord_name, 
                        landlord_rating, 
                        landlord_review, 
                        total_rent, 
                        ind_rent, 
                        utilities, 
                        parking):

        pid = self.get_pid_from_address_display(address)
        resp_date = str(datetime.date.today())
        
        sql = """
            INSERT INTO tResponse (pid, resp_date, property_rating, property_review, 
                                    landlord_name, landlord_rating, landlord_review, 
                                    total_rent, ind_rent, utilities, parking)
                                    
            VALUES (:pid_input, :r_date, :p_rate, :p_rev, :l_name, :l_rate, :l_rev, :t_rent, :i_rent, :util, :park)
        ;"""
        
        
        
        self.run_action(sql, params={'pid_input':pid, 
                                   'r_date':resp_date, 
                                   'p_rate':property_rating, 
                                   'p_rev':property_review, 
                                   'l_name':landlord_name, 
                                   'l_rate':landlord_rating, 
                                   'l_rev':landlord_review, 
                                   't_rent':total_rent, 
                                   'i_rent':ind_rent,
                                   'util':utilities,
                                   'park':parking
                                  }, keep_open=True)
        self._conn.commit()
        self._close()
        return
    