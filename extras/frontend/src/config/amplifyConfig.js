const amplifyConfig = {
  Auth: {
    // Replace these values with your actual Cognito details
    region: 'us-east-1',
    userPoolId: 'us-east-1_ppj5bg85q',
    userPoolWebClientId: '47ie1g8drh3d048sa27t7rjf56',
    mandatorySignIn: true,
    authenticationFlowType: 'USER_SRP_AUTH'
  }
};

export default amplifyConfig; 