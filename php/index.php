<?php
	error_reporting(E_ALL ^ E_STRICT);
	require('parser.php');
	require('doubletalk.php');
	
	//if(!isset($_GET['code']) || empty($_GET['code']))
	//	die();
	
	//$code = $_GET['code'];
	
	$DTKint = new DTKInterpreter($DTKlang);
	//$DTKint->load($code, DTKinterpreter::SOURCE_TEXT);
	$DTKint->load('sample.dtk', DTKinterpreter::SOURCE_FILE);
	//$DTKint->passthrough();
	$DTKint->exec();
?>