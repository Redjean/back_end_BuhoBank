from .database import customer_collection,account_collection
from .models import CustomerModel
from .models import LogInModel
from .models import UpdatePass,EmailParams,id_clinet
from bson import ObjectId
import bcrypt
import resend
from fastapi import FastAPI, HTTPException, Depends
import os
import random



async def add_customer(customer_data: CustomerModel) -> dict:
    # Hashear la contraseña antes de almacenarla
    hashed_password = bcrypt.hashpw(customer_data.password.encode('utf-8'), bcrypt.gensalt())
   # Convertir el modelo a un diccionario serializable
    customer_dict = customer_data.dict(by_alias=True)
    customer_dict['password'] = hashed_password.decode('utf-8')  
    del customer_dict['pass_conf']
    customer_dict['accounts'] = []
    try:
        result = await customer_collection.insert_one(customer_dict)
        
        # Verificar si la inserción fue exitosa
        if result.inserted_id:
            account_model = id_clinet(id=str(result.inserted_id))
            await create_new_bank_account(account_model)
            return True
        else:
            return False
    except Exception as e:
            print(f"Error al insertar el cliente: {e}")
            return False


async def update_customer(credentials: CustomerModel) -> dict:
    # Hashear la nueva contraseña antes de almacenarla
    hashed_password = bcrypt.hashpw(credentials.password.encode('utf-8'), bcrypt.gensalt())

    # Crear el diccionario con los campos a actualizar
    update_data = {
        "user": credentials.user,
        "password": hashed_password.decode('utf-8')
    }

    result = await customer_collection.update_one(
        {"ci": credentials.ci},
        {"$set": update_data}
    )

    if result.modified_count > 0:
       return True
    else:
        return False

async def fetchAcounts(list_accounts):
    accounts_data=[]
    for account in list_accounts:
        query={
            "account_number":account
        }

        account_data=await account_collection.find_one(query)
        del account_data['_id']
        if accounts_data is None:
            print("No existe la cuenta")
        else:
            accounts_data.append(account_data)
    return accounts_data





async def checkData(credentials: LogInModel) -> bool:
    query = {
        "user": credentials.user
    }
    user = await customer_collection.find_one(query)
    if user is None:
        print(f"Usuario {credentials.user} no encontrado")
        return False
    else:
        print(f"Usuario {credentials.user} encontrado con exito")
    
    hashed_password=user.get('password','')
    accounts_data_response=await fetchAcounts(user['accounts'])
    print(accounts_data_response)
    if bcrypt.checkpw(credentials.password.encode('utf-8'), hashed_password.encode('utf-8')):

        return True,accounts_data_response,user['_id']
    else:
        return False
    
#función para verificar que la nueva contraseña cumple con los requisitos mínimos
async def update_password(data: UpdatePass) -> dict:
    # Buscar el usuario por su ID
    customer = await customer_collection.find_one({"_id": ObjectId(data.user_id)})
    if not customer:
        return {"code": "USER_NOT_FOUND"}

    # Verificar si la contraseña actual es correcta
    if not bcrypt.checkpw(data.current_password.encode('utf-8'), customer['password'].encode('utf-8')):
        return {"code": "INCORRECT_CURRENT_PASSWORD"}

    # Hashear la nueva contraseña antes de almacenarla
    hashed_password = bcrypt.hashpw(data.new_password.encode('utf-8'), bcrypt.gensalt())
    
    # Actualizar la contraseña en la base de datos
    await customer_collection.update_one(
        {"_id": ObjectId(data.user_id)},
        {"$set": {"password": hashed_password.decode('utf-8')}}
    )
    
    return {"message": "Contraseña cambiada exitosamente"}


async def send_email(params: EmailParams) -> dict:
    resend.api_key = os.environ["RESEND_API_KEY"]
    code=random.randint(100000, 999999)
    try:
        email_params: resend.Emails.SendParams = {
            "from": "onboarding@resend.dev",
            "to": params.to,
            "subject": "code_verify",
            "html": f"<strong>{code}</strong>",
        }
        email: resend.Email = resend.Emails.send(email_params)
        return {"status": "success", "email_id": email}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
async def number_account():
    account=random.randint(10000000, 99999999)
    query={
        "numero_cuenta": account
    }
    account_data = await customer_collection.find_one(query)
    if account_data is None:
        return account
    



async def add_new_bank_account(num_account):
    new_account={
        "account_number":num_account,
        "balance":0.0,
        "movements":{
            
        }
    }
    
    result = await account_collection.insert_one(new_account)
    if result.inserted_id:
        return True
    else:
        return False
    



async def create_new_bank_account(id:id_clinet)-> dict:
    account=await number_account()
    user_data=await customer_collection.find_one({"_id": ObjectId(id.id)})
    current_accounts=user_data['accounts']
    current_accounts.append(account)
    user_data['accounts']=current_accounts
    result = await customer_collection.update_one(
       {"_id": ObjectId(id.id)},
       {"$set": {"accounts": current_accounts}}
    )
    
    if result.modified_count > 0:
        print("se modifico")
        new_account=await add_new_bank_account(account)
        if new_account:
            return {"CODE":"NEW_ACCOUNT_CREATED"}
        else:
            return {"CODE":"NEW_ACCOUNT_DONT_CREATED"}
        
    else:
        print("dea a malas")
    

    