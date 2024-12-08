const StudentEnrollment = artifacts.require("StudentEnrollment");

module.exports = function(deployer) {
  deployer.deploy(StudentEnrollment);
}; 