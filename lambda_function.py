import json
import boto3
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize the Bedrock Agent Runtime client
bedrock_agent = boto3.client(service_name='bedrock-agent-runtime')

def lambda_handler(event, context):
    logger.info("Lambda function invoked")
    logger.info(f"Event received: {json.dumps(event)}")
    
    try:
        # Capture data from your HTML form
        body = json.loads(event.get('body', '{}'))
        logger.info(f"Parsed body: {body}")
        
        # 1. Identify if this is a calculation or a follow-up chat
        if body.get('isChat'):
            # It's a follow-up question!
            prompt = body.get('message', 'Hello!')
            logger.info(f"Chat prompt: {prompt}")
        else:
            # 1. Capture data from your HTML form
            age = int(body.get('age', 0))
            current_savings = float(body.get('savings', 0))
            monthly_save = float(body.get('monthly', 0))
            college_type = body.get('collegeType', 'inState')
            risk_style = body.get('riskStyle', 'balanced')
            
            logger.info(f"Inputs - Age: {age}, Savings: {current_savings}, Monthly Save: {monthly_save}, College Type: {college_type}, Risk Style: {risk_style}")
            
            # 2. Math Logic (Constants from your project plan)
            tuition_map = {"inState": 12000, "outOfState": 28000, "private": 45000}
            return_map = {"conservative": 0.04, "balanced": 0.06, "growth": 0.08}
            
            years_to_college = 18 - age
            annual_cost = tuition_map[college_type]
            
            logger.info(f"Years to college: {years_to_college}, Annual Cost: {annual_cost}")
            
            # Calculate Future Cost (5% inflation)
            total_future_cost = (annual_cost * (1.05 ** years_to_college)) * 4
            logger.info(f"Total Future Cost: {total_future_cost}")
            
            # Calculate Projected Savings (Future Value of Annuity)
            r = return_map[risk_style] / 12
            n = years_to_college * 12
            projected_savings = (current_savings * (1 + r)**n) + (monthly_save * (((1 + r)**n - 1) / r))
            logger.info(f"Projected Savings: {projected_savings}")
            
            gap = total_future_cost - projected_savings
            status = "On Track" if gap <= 0 else "Slightly Behind" if gap < 50000 else "At Risk"
            logger.info(f"Gap: {gap}, Status: {status}")
            
            # Create the initial advisor prompt
            prompt = (f"Student age: {age}, College: {college_type}, Style: {risk_style}, "
                      f"Tuition: ${total_future_cost:,.2f}, Savings: ${projected_savings:,.2f}, "
                      f"Gap: ${gap:,.2f}, Status: {status}")
            logger.info(f"Generated prompt: {prompt}")

        # 3. Call the Bedrock Agent
        AGENT_ID = 'LVAP5E9ECG'
        AGENT_ALIAS_ID = 'RAIOTFSOPE'
        logger.info(f"Calling Bedrock Agent with Agent ID: {AGENT_ID}, Alias ID: {AGENT_ALIAS_ID}")
        
        raw_completion = bedrock_agent.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=AGENT_ALIAS_ID,
            sessionId=body.get('sessionId', 'hackathon-session-123'),
            inputText=prompt
        )
        logger.info(f"Bedrock Agent response: {raw_completion}")
        
        # Extract the text response from the Agent
        completion = ""

        try:
            if "completion" in raw_completion:
                for event in raw_completion["completion"]:
                    if "chunk" in event and "bytes" in event["chunk"]:
                        completion += event["chunk"]["bytes"].decode("utf-8")
        except Exception as e:
            logger.error("Error reading Bedrock stream", exc_info=True)


        # Final check if AI is silent
        if not completion:
            completion = "The AI Coach is analyzing your request..."
            logger.info("No completion received from the agent. Using fallback message.")

        if body.get('isChat'):

            return {
                'statusCode': 200,
                'body': json.dumps({'answer': completion})
            }

        response = {
            "statusCode": 200,
            "body": json.dumps({
                "message": completion,
                "projectedSavings": projected_savings,
                "totalFutureCost": total_future_cost
            })
        }
        logger.info(f"Response: {response}")
        return response
        
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'answer': f"System Error: {str(e)}"})
        }
