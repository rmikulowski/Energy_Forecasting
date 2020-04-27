from gurobipy import *
import pandas as pd

def deterministic(forecasting_since, forecasting_till, storage_bid, storage_parameters, prices, demand, output_flag = False, saving_storage = False):
    """
    This function will optimize bid based on:
    - time of auction (forecasting_since, forecasting_till),
    - price of storage (storage_bid),
    - parameters of auction (storage_parameters),
    - one scenario (prices, demand).
    Additionally, output_flag defines if program should print optimization parameters. Default False, for faster compilation time.
    saving_storage defines if all variables should be saved as true_variables (False), or if just capacity of storage should be saved (True). 

    This function should be used for optimization with fixed product range with no possibility of additional flexibility.
    """

    # Parameters of auction for storage
    storage_available, default_in_rate, default_out_rate, price_injection, limit_buying, limit_selling = storage_parameters
    
    ### Defining parameters to be calculated

    # time - number of days of the forecast
    # Has to be adjusted in case of public holiday flow
    time = (pd.to_datetime(forecasting_till) - pd.to_datetime(forecasting_since)).days - demand[~demand.index.isin(prices.index)].shape[0] + 1
    demand = demand[demand.index.isin(prices.index)]

    # Creating a model which is MIP - mixed-integer programming model
    m = Model("mip1")
    m.setParam( 'OutputFlag', output_flag )

    #-----------------------------------------#

    ### Setting variables

    # Production level in spot market
    g_spot = m.addVars(time, vtype = GRB.CONTINUOUS, name = 'g_spot', lb = -limit_selling, ub = limit_buying)

    # Storage capacity
    st_max = m.addVar(vtype = GRB.CONTINUOUS, name = 'st_max', lb = 0, ub = storage_available)

    # Storage level
    st = m.addVars(time, vtype = GRB.CONTINUOUS, name = "st", lb = 0)

    # Storage injection level
    st_in = m.addVars(time, vtype = GRB.CONTINUOUS, name = 'st_in', lb = 0)

    # Storage withdrawal level
    st_out = m.addVars(time, vtype = GRB.CONTINUOUS, name = 'st_out', lb = 0)

    # If payment via injection or whole storage
    u_st = m.addVar(vtype = GRB.BINARY, name = 'u_st')


    #-----------------------------------------#

    ### Objective function

    # Defining cost of storage
    cost_storage = storage_bid * st_max + (u_st * st_in.sum() + (1 - u_st) * st_max) * price_injection 

    # Defining cost of trading on spot market
    cost_trading = sum(g_spot[t] * prices.iloc[t] for t in range(time))

    m.setObjective(cost_storage + cost_trading, GRB.MINIMIZE)

    #-----------------------------------------#

    ### Setting constraints

    # Demand and supply balance of Day-Ahead market
    m.addConstrs(g_spot[t] - st_in[t] + st_out[t] == demand.iloc[t] for t in range(time))

    # Max capacity of the storage
    m.addConstrs(st[t] <= st_max for t in range(time))

    # Max injection and withdrawal
    m.addConstrs(st_in[t] <= 1/default_in_rate * st_max for t in range(time)) # 
    m.addConstrs(st_out[t] <= 1/default_out_rate * st_max for t in range(time))


    # Flow in the storage
    m.addConstr(st[0] == 0)
    m.addConstrs(st[t-1] + st_in[t-1] - st_out[t-1] == st[t] for t in range(1,time))
    m.addConstr(st[time-1] == 0)

    #-----------------------------------------#

    ### Optimization

    m.optimize()

    if saving_storage:
        result_variables = st_max.x
    else:
        result_variables = pd.DataFrame(columns = ['Names','Values'])
        for i in range(len(m.getVars())):
            v = m.getVars()[i]
            result_variables.loc[i] = [v.varName, v.x]        

    result_optimization = m.objVal

    return result_optimization, result_variables


def additional_flexibility_full(forecasting_since, forecasting_till, storage_bid, storage_parameters, limit_trading, prices, demand, output_flag = False):
    """
    This function will optimize bid based on:
    - time of auction (forecasting_since, forecasting_till),
    - price of storage (storage_bid),
    - parameters of auction (storage_parameters),
    - bounds for trading (limit_trading) - same values for selling and buying
    - one scenario (prices, demand).
    Additionally, output_flag defines if program should print optimization parameters. Default False, for faster compilation time.

    This function should be used for optimization with fixed product range with possibility of additional flexibility.
    """

    storage_available, default_in_rate, default_out_rate, min_in_rate, min_out_rate, add_price_injection, add_price_withdrawal, price_injection = storage_parameters
    
    ### Defining parameters to be calculated

    # time - number of days of the forecast
    # Has to be adjusted in case of public holiday flow
    time = (pd.to_datetime(forecasting_till) - pd.to_datetime(forecasting_since)).days - demand[~demand.index.isin(prices.index)].shape[0] + 1
    demand = demand[demand.index.isin(prices.index)]

    # Creating a model which is MIP - mixed-integer programming model
    m = Model("mip1")
    m.setParam( 'OutputFlag', output_flag )

    #-----------------------------------------#

    ### Setting variables

    # Production level in spot market
    g_spot = m.addVars(time, vtype = GRB.CONTINUOUS, name = 'g_spot', lb = -limit_trading, ub = limit_trading)

    # Storage capacity
    st_max = m.addVar(vtype = GRB.CONTINUOUS, name = 'st_max', lb = 0, ub = storage_available)

    # Storage level
    st = m.addVars(time, vtype = GRB.CONTINUOUS, name = "st", lb = 0)

    # Storage injection level
    st_in = m.addVars(time, vtype = GRB.CONTINUOUS, name = 'st_in', lb = 0)

    # Storage withdrawal level
    st_out = m.addVars(time, vtype = GRB.CONTINUOUS, name = 'st_out', lb = 0)

    # If payment via injection or whole storage
    u_st = m.addVar(vtype = GRB.BINARY, name = 'u_st')


    #-----------------------------------------#

    ### Objective function

    # Defining cost of storage
    price_additional_injecting = 1 / (default_in_rate * 24) * add_price_injection * (default_in_rate/min_in_rate - 1)
    price_additional_withdrawal = 1 / (default_out_rate * 24) * add_price_withdrawal * (default_out_rate/min_out_rate - 1)
    cost_storage = (storage_bid + price_additional_injecting + price_additional_withdrawal) * st_max + (u_st * st_in.sum() + (1 - u_st) * st_max) * price_injection 

    # Defining cost of trading on spot market
    cost_trading = sum(g_spot[t] * prices.iloc[t] for t in range(time))

    m.setObjective(cost_storage + cost_trading, GRB.MINIMIZE)

    #-----------------------------------------#

    ### Setting constraints

    # Demand and supply balance of Day-Ahead market
    m.addConstrs(g_spot[t] - st_in[t] + st_out[t] == demand.iloc[t] for t in range(time))

    # Max capacity of the storage
    m.addConstrs(st[t] <= st_max for t in range(time))

    # Max injection and withdrawal
    m.addConstrs(st_in[t] <= 1/min_in_rate * st_max for t in range(time)) # 
    m.addConstrs(st_out[t] <= 1/min_out_rate * st_max for t in range(time))


    # Flow in the storage
    m.addConstr(st[0] == 0)
    m.addConstrs(st[t-1] + st_in[t-1] - st_out[t-1] == st[t] for t in range(1,time))
    m.addConstr(st[time-1] == 0)

    #-----------------------------------------#

    ### Optimization

    m.optimize()

    result_variables = pd.DataFrame(columns = ['Names','Values'])
    for i in range(len(m.getVars())):
        v = m.getVars()[i]
        result_variables.loc[i] = [v.varName, v.x]
    result_optimization = m.objVal

    return result_optimization, result_variables



def additional_flexibility(forecasting_since, forecasting_till, st_max, storage_bid, storage_parameters, limit_trading, prices, demand, output_flag = False, saving_storage = False):
    """
    This function will optimize product range based on:
    - time of auction (forecasting_since, forecasting_till),
    - capacity of storage (st_max)
    - price of storage (storage_bid),
    - parameters of auction (storage_parameters),
    - bounds for trading (limit_trading) - same values for selling and buying
    - one scenario (prices, demand).
    Additionally, output_flag defines if program should print optimization parameters. Default False, for faster compilation time.
    saving_storage defines if all variables should be saved as true_variables (False), or if just capacity of storage should be saved (True). 

    This function should be used for optimization with fixed product range.
    """

    storage_in_max, storage_out_max, cost_in_additional, cost_out_additional, storage_in_additional, storage_out_additional, price_injection = storage_parameters
    
    ### Defining parameters to be calculated

    # time - number of days of the forecast
    # Has to be adjusted in case of public holiday flow
    time = (pd.to_datetime(forecasting_till) - pd.to_datetime(forecasting_since)).days - demand[~demand.index.isin(prices.index)].shape[0] + 1
    demand = demand[demand.index.isin(prices.index)]

    # Creating a model which is MIP - mixed-integer programming model
    m = Model("mip1")
    m.setParam( 'OutputFlag', output_flag )

    #-----------------------------------------#

    ### Setting variables

    # Production level in spot market
    g_spot = m.addVars(time, vtype = GRB.CONTINUOUS, name = 'g_spot', lb = -limit_trading, ub = limit_trading)

    # Storage level
    st = m.addVars(time, vtype = GRB.CONTINUOUS, name = "st", lb = 0)

    # Storage injection level
    st_in = m.addVars(time, vtype = GRB.CONTINUOUS, name = 'st_in', lb = 0)
    st_in_additional = m.addVar(vtype = GRB.CONTINUOUS, lb = 1, ub = (storage_in_additional), name = 'st_in_additional')

    # Storage withdrawal level
    st_out = m.addVars(time, vtype = GRB.CONTINUOUS, name = 'st_out', lb = 0)
    st_out_additional = m.addVar(vtype = GRB.CONTINUOUS, lb = 1, ub = (storage_out_additional), name = 'st_out_additional')

    # If payment via injection or whole storage
    u_st = m.addVar(vtype = GRB.BINARY, name = 'u_st')


    #-----------------------------------------#

    ### Objective function

    # Defining cost of storage
    price_additional_injecting =  (1/storage_in_max) / 24 * cost_in_additional * (st_in_additional - 1)
    price_additional_withdrawal = (1/storage_out_max) / 24 * cost_out_additional * (st_out_additional - 1)
    cost_storage = (storage_bid + price_additional_injecting + price_additional_withdrawal) * st_max + (u_st * st_in.sum() + (1 - u_st) * st_max) * price_injection 

    # Defining cost of trading on spot market
    cost_trading = sum(g_spot[t] * prices.iloc[t] for t in range(time))

    m.setObjective(cost_storage + cost_trading, GRB.MINIMIZE)

    #-----------------------------------------#

    ### Setting constraints

    # Demand and supply balance of Day-Ahead market
    m.addConstrs(g_spot[t] - st_in[t] + st_out[t] == demand.iloc[t] for t in range(time))

    # Max capacity of the storage
    m.addConstrs(st[t] <= st_max for t in range(time))

    # Max injection and withdrawal
    m.addConstrs(st_in[t] <= (1/storage_in_max) * st_max * (st_in_additional) for t in range(time)) # 
    m.addConstrs(st_out[t] <= (1/storage_out_max) * st_max * (st_out_additional) for t in range(time))


    # Flow in the storage
    m.addConstr(st[0] == 0)
    m.addConstrs(st[t-1] + st_in[t-1] - st_out[t-1] == st[t] for t in range(1,time))
    m.addConstr(st[time-1] == 0)

    #-----------------------------------------#

    ### Optimization

    m.optimize()

    if saving_storage:
        result_variables = st_max.x
    else:
        result_variables = pd.DataFrame(columns = ['Names','Values'])
        for i in range(len(m.getVars())):
            v = m.getVars()[i]
            result_variables.loc[i] = [v.varName, v.x]        

    result_optimization = m.objVal

    return result_optimization, result_variables


def stochastic(forecasting_since, forecasting_till, storage_bid, storage_parameters, prices_GPN, prices_WD, demand, demand_WD, output_flag = True):
    """
    # Here: all the description
    """

    storage_available, storage_in_max, storage_out_max, price_injection = storage_parameters

    ### Defining parameters to be calculated

    # time - number of days of the forecast
    time = (pd.to_datetime(forecasting_till) - pd.to_datetime(forecasting_since)).days + 1

    scenarios_WD = len(prices_GPN) * len(prices_WD) * demand.shape[0] * demand_WD.iloc[0,0].shape[0] 
    scenarios_DA = len(prices_GPN) * demand.shape[0]

    # Creating a model which is MIP - mixed-integer programming model
    m = Model("mip1")
    m.setParam( 'OutputFlag', output_flag )

    #-----------------------------------------#

    ### Setting variables


    #---------------------#
    ## First stage decision variables
    # If payment via injection or whole storage
    u_st = m.addVar(vtype = GRB.BINARY, name = 'u_st')

    # Storage capacity
    st_max = m.addVar(vtype = GRB.CONTINUOUS, name = 'st_max', lb = 0, ub = storage_available)

    #---------------------#
    ## Second stage decision variables (Day-ahead)
    # Production level in spot market
    g_DA = m.addVars(time, scenarios_DA, vtype = GRB.CONTINUOUS, name = 'g_DA', lb = -GRB.INFINITY)

    # Storage level from DA perspective
    st_DA = m.addVars(time, scenarios_DA, vtype = GRB.CONTINUOUS, name = "st_DA", lb = 0)

    # Storage injection level from DA perspective
    st_in_DA = m.addVars(time, scenarios_DA, vtype = GRB.CONTINUOUS, name = 'st_in_DA', lb = 0)

    # Storage withdrawal level from DA perspective
    st_out_DA = m.addVars(time, scenarios_DA, vtype = GRB.CONTINUOUS, name = 'st_out_DA', lb = 0)

    #---------------------#
    ## Third stage decision variables (Within-day)
    # Production level in spot market
    g_WD = m.addVars(time, scenarios_WD, vtype = GRB.CONTINUOUS, name = 'g_WD', lb = -GRB.INFINITY)

    # Storage level from WD perspective
    st_WD = m.addVars(time, scenarios_WD, vtype = GRB.CONTINUOUS, name = "st_WD", lb = 0)

    # Storage injection level from WD perspective
    st_in_WD = m.addVars(time, scenarios_WD, vtype = GRB.CONTINUOUS, name = 'st_in_WD', lb = 0)

    # Storage withdrawal level from WD perspective
    st_out_WD = m.addVars(time, scenarios_WD, vtype = GRB.CONTINUOUS, name = 'st_out_WD', lb = 0)


    #-----------------------------------------#

    ### Objective function

    # Defining cost of storage
    cost_storage = storage_bid * st_max + (sum(u_st * st_in_WD.sum(t,'*')/scenarios_WD for t in range(time)) + (1 - u_st) * st_max) * price_injection 

    # Defining cost of trading on spot market
    cost_trading_DA = sum(g_DA[t, (demand.shape[0] * i + j)] * prices_GPN.iloc[i][t] for t in range(time) for i in range(len(prices_GPN)) for j in range(demand.shape[0]) ) / scenarios_DA

    # Defining cost of trading on spot market
    cost_trading_WD = sum(g_WD[t, (demand_WD.iloc[0,0].shape[0]*(len(prices_WD)*(demand.shape[0] * i + j)+k)+l)] * prices_WD.iloc[k][t] for t in range(time) for i in range(len(prices_GPN)) for j in range(demand.shape[0]) for k in range(len(prices_WD)) for l in range(demand_WD.iloc[0,0].shape[0])) / scenarios_WD

    m.setObjective(cost_storage + cost_trading_DA + cost_trading_WD, GRB.MINIMIZE)

    #-----------------------------------------#

    ### Setting constraints

    for t in range(time):
        for i in range(len(prices_GPN)):
            for j in range(demand.shape[0]):
                a = (demand.shape[0] * i + j)
                # Demand and supply balance of Day-Ahead market
                m.addConstr(g_DA[t,a] - st_in_DA[t,a] + st_out_DA[t,a] == demand.iloc[j,t])

                # Max capacity of the storage
                m.addConstr(st_DA[t,a] <= st_max)

                # Max injection and withdrawal
                m.addConstr(st_in_DA[t,a] <= (storage_in_max) * st_max)
                m.addConstr(st_out_DA[t,a] <= (storage_out_max) * st_max)

                # Flow in the storage
                m.addConstr(st_DA[0,a] == 0)
                m.addConstr(st_DA[time-1,a] == 0)
                if t != 0:
                    m.addConstr(st_DA[t-1, a] + st_in_DA[t-1, a] - st_out_DA[t-1, a] == st_DA[t, a])
                m.addConstr(st_out_DA[time-1,a] == 0)

                for k in range(len(prices_WD)):
                    for l in range(demand_WD.iloc[0,0].shape[0]):
                        # Defining aux parameter, which is used for 
                        b = (demand_WD.iloc[0,0].shape[0]*(len(prices_WD)*a+k)+l)

                        # Demand and supply balance of changes that have to be done on Within-Day market 
                        m.addConstr(g_WD[t,b] - (st_in_DA[t,a] - st_in_WD[t,b]) + (st_out_DA[t,a] - st_out_WD[t,b]) == (demand.iloc[j,t] - demand_WD.iloc[j,t][l]))

                        # Max capacity of the storage
                        m.addConstr(st_WD[t,b] <= st_max)
    
                        # Max injection and withdrawal
                        m.addConstr(st_in_WD[t,b] <= (storage_in_max) * st_max)
                        m.addConstr(st_out_WD[t,b] <= (storage_out_max) * st_max)

                        # Flow in the storage
                        m.addConstr(st_WD[0,b] == 0)
                        m.addConstr(st_WD[time-1,b] == 0)
                        if t != 0:
                            m.addConstr(st_WD[t-1, b] + st_in_WD[t-1, b] - st_out_WD[t-1, b] == st_WD[t, b])

    
    #-----------------------------------------#

    ### Optimization

    m.optimize()

    result_variables = pd.DataFrame(columns = ['Names','Values'])
    for i in range(len(m.getVars())):
        v = m.getVars()[i]
        result_variables.loc[i] = [v.varName, v.x]
    result_optimization = m.objVal

    return result_optimization, result_variables



def additional_flexibility_stochastic(forecasting_since, forecasting_till, st_max, storage_bid, storage_parameters, prices_GPN, prices_WD, demand, demand_WD, output_flag = True):
    """
    # Here: all the description
    """

    storage_in_max, storage_out_max, cost_in_additional, cost_out_additional, storage_in_additional, storage_out_additional, price_injection = storage_parameters

    ### Defining parameters to be calculated

    # time - number of days of the forecast
    time = (pd.to_datetime(forecasting_till) - pd.to_datetime(forecasting_since)).days + 1

    scenarios_WD = len(prices_GPN) * len(prices_WD) * demand.shape[0] * demand_WD.iloc[0,0].shape[0] 
    scenarios_DA = len(prices_GPN) * demand.shape[0]

    # Creating a model which is MIP - mixed-integer programming model
    m = Model("mip1")
    m.setParam( 'OutputFlag', output_flag )

    #-----------------------------------------#

    ### Setting variables


    #---------------------#
    ## First stage decision variables
    # If payment via injection or whole storage
    u_st = m.addVar(vtype = GRB.BINARY, name = 'u_st')

    st_in_additional = m.addVar(vtype = GRB.CONTINUOUS, lb = 0, ub = (storage_in_additional - 1), name = 'st_in_additional')
    st_out_additional = m.addVar(vtype = GRB.CONTINUOUS, lb = 0, ub = (storage_out_additional - 1), name = 'st_out_additional')


    #---------------------#
    ## Second stage decision variables (Day-ahead)
    # Production level in spot market
    g_DA = m.addVars(time, scenarios_DA, vtype = GRB.CONTINUOUS, name = 'g_DA', lb = -GRB.INFINITY)

    # Storage level from DA perspective
    st_DA = m.addVars(time, scenarios_DA, vtype = GRB.CONTINUOUS, name = "st_DA", lb = 0)

    # Storage injection level from DA perspective
    st_in_DA = m.addVars(time, scenarios_DA, vtype = GRB.CONTINUOUS, name = 'st_in_DA', lb = 0)

    # Storage withdrawal level from DA perspective
    st_out_DA = m.addVars(time, scenarios_DA, vtype = GRB.CONTINUOUS, name = 'st_out_DA', lb = 0)

    #---------------------#
    ## Third stage decision variables (Within-day)
    # Production level in spot market
    g_WD = m.addVars(time, scenarios_WD, vtype = GRB.CONTINUOUS, name = 'g_WD', lb = -GRB.INFINITY)

    # Storage level from WD perspective
    st_WD = m.addVars(time, scenarios_WD, vtype = GRB.CONTINUOUS, name = "st_WD", lb = 0)

    # Storage injection level from WD perspective
    st_in_WD = m.addVars(time, scenarios_WD, vtype = GRB.CONTINUOUS, name = 'st_in_WD', lb = 0)

    # Storage withdrawal level from WD perspective
    st_out_WD = m.addVars(time, scenarios_WD, vtype = GRB.CONTINUOUS, name = 'st_out_WD', lb = 0)


    #-----------------------------------------#

    ### Objective function

    # Defining cost of storage
    price_additional_injecting =  storage_in_max / 24 * cost_in_additional * (st_in_additional)
    price_additional_withdrawal = storage_out_max / 24 * cost_out_additional * (st_out_additional)
    cost_storage = (storage_bid + price_additional_injecting + price_additional_withdrawal) * st_max + (sum(u_st * st_in_WD.sum(t,'*')/scenarios_WD for t in range(time)) + (1 - u_st) * st_max) * price_injection 

    # Defining cost of trading on spot market
    cost_trading_DA = sum(g_DA[t, (demand.shape[0] * i + j)] * prices_GPN.iloc[i][t] for t in range(time) for i in range(len(prices_GPN)) for j in range(demand.shape[0]) ) / scenarios_DA

    # Defining cost of trading on spot market
    cost_trading_WD = sum(g_WD[t, (demand_WD.iloc[0,0].shape[0]*(len(prices_WD)*(demand.shape[0] * i + j)+k)+l)] * prices_WD.iloc[k][t] for t in range(time) for i in range(len(prices_GPN)) for j in range(demand.shape[0]) for k in range(len(prices_WD)) for l in range(demand_WD.iloc[0,0].shape[0])) / scenarios_WD

    m.setObjective(cost_storage + cost_trading_DA + cost_trading_WD, GRB.MINIMIZE)

    #-----------------------------------------#

    ### Setting constraints

    for t in range(time):
        for i in range(len(prices_GPN)):
            for j in range(demand.shape[0]):
                a = (demand.shape[0] * i + j)
                # Demand and supply balance of Day-Ahead market
                m.addConstr(g_DA[t,a] - st_in_DA[t,a] + st_out_DA[t,a] == demand.iloc[j,t])

                # Max capacity of the storage
                m.addConstr(st_DA[t,a] <= st_max)

                # Max injection and withdrawal
                m.addConstr(st_in_DA[t,a] <= (storage_in_max) * st_max * (st_in_additional + 1))
                m.addConstr(st_out_DA[t,a] <= (storage_out_max) * st_max * (st_out_additional + 1))

                # Flow in the storage
                m.addConstr(st_DA[0,a] == 0)
                m.addConstr(st_DA[time-1,a] == 0)
                if t != 0:
                    m.addConstr(st_DA[t-1, a] + st_in_DA[t-1, a] - st_out_DA[t-1, a] == st_DA[t, a])
                m.addConstr(st_out_DA[time-1,a] == 0)

                for k in range(len(prices_WD)):
                    for l in range(demand_WD.iloc[0,0].shape[0]):
                        # Defining aux parameter, which is used for 
                        b = (demand_WD.iloc[0,0].shape[0]*(len(prices_WD)*a+k)+l)

                        # Demand and supply balance of changes that have to be done on Within-Day market 
                        m.addConstr(g_WD[t,b] - (st_in_DA[t,a] - st_in_WD[t,b]) + (st_out_DA[t,a] - st_out_WD[t,b]) == (demand.iloc[j,t] - demand_WD.iloc[j,t][l]))

                        # Max capacity of the storage
                        m.addConstr(st_WD[t,b] <= st_max)
    
                        # Max injection and withdrawal
                        m.addConstr(st_in_WD[t,b] <= (storage_in_max) * st_max * (st_in_additional + 1))
                        m.addConstr(st_out_WD[t,b] <= (storage_out_max) * st_max * (st_in_additional + 1))

                        # Flow in the storage
                        m.addConstr(st_WD[0,b] == 0)
                        m.addConstr(st_WD[time-1,b] == 0)
                        if t != 0:
                            m.addConstr(st_WD[t-1, b] + st_in_WD[t-1, b] - st_out_WD[t-1, b] == st_WD[t, b])

    
    #-----------------------------------------#

    ### Optimization

    m.optimize()

    result_variables = pd.DataFrame(columns = ['Names','Values'])
    for i in range(len(m.getVars())):
        v = m.getVars()[i]
        result_variables.loc[i] = [v.varName, v.x]
    result_optimization = m.objVal

    return result_optimization, result_variables
