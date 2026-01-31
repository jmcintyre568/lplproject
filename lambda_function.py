import json
import boto3

# Initialize the Bedrock Agent Runtime client
bedrock_agent = boto3.client(service_name='bedrock-agent-runtime')

def lambda_handler(event, context):
    # 1. Capture data from your HTML form
    body = json.loads(event['body'])
    age = int(body['age'])
    current_savings = float(body['savings'])
    monthly_save = float(body['monthly'])
    college_type = body['collegeType']
    risk_style = body['riskStyle']
    
    # 2. Math Logic (Constants from your project plan)
    tuition_map = {"inState": 12000, "outOfState": 28000, "private": 45000}
    return_map = {"conservative": 0.04, "balanced": 0.06, "growth": 0.08}
    
    years_to_college = 18 - age
    annual_cost = tuition_map[college_type]
    
    # Calculate Future Cost (5% inflation)
    total_future_cost = (annual_cost * (1.05 ** years_to_college)) * 4
    
    # Calculate Projected Savings 
    r = return_map[risk_style] / 12
    n = years_to_college * 12
    projected_savings = (current_savings * (1 + r)**n) + (monthly_save * (((1 + r)**n - 1) / r))
    
    gap = total_future_cost - projected_savings
    status = "On Track" if gap <= 0 else "Slightly Behind" if gap < 50000 else "At Risk"
    
    # 3. call the Bedrock Agent
    AGENT_ID = 'LVAP5E9ECG'
    AGENT_ALIAS_ID = '0TBO49NONJ'
    
    prompt = f"Student age: {age}, College: {college_type}, Style: {risk_style}, Tuition: ${total_future_cost:,.2f}, Savings: ${projected_savings:,.2f}, Gap: ${gap:,.2f}, Status: {status}"
    
    response = bedrock_agent.invoke_agent(
        agentId=AGENT_ID,
        agentAliasId=AGENT_ALIAS_ID,
        sessionId='hackathon-session-123',
        inputText=prompt
    )
    
    # Extract the text response from the Agent
    completion = ""
    for event in response.get('completion'):
        chunk = event.get('chunk')
        if chunk:
            completion += chunk.get('bytes').decode()

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*', 
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,POST'
        },
        'body': json.dumps({'answer': completion})
    }