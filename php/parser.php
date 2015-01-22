<?php
class Token{
	public $symbol;
	public $line;
	public $char;
	public $type;
		
	public function Token($symbol = null, $type = null, $line = null, $char = null){
		$this->symbol	= $symbol;
		$this->line		= $line;
		$this->char		= $char;
		$this->type		= $type;
	}
			
	public function __toString(){
		global $TOKEN_TYPES;
		return sprintf("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>", 
			$this->line, 
			$this->char, 
			$this->symbol, 
			$TOKEN_TYPES[$this->type]
		);
	}
}

class InternalInstruction{
	
}

class Keyword extends Token{
	public $argument;
	
	public function Keyword(Token $token, $arg = null){
		$this->symbol	= $token->symbol;
		$this->line		= $token->line;
		$this->char		= $token->char;
		$this->argument	= $arg;
	}
}

class Variable extends Token{
	public $address;

	public function Variable(Token $token, &$address){
		$this->symbol	= $token->symbol;
		$this->line 	= $token->line;
		$this->char		= $token->char;
		$this->address	=& $address;
	}
	
}

class ConditionalBlock extends Keyword{
	public $begin;
	public $falseBlock;
	public $end;
	
	public function ConditionalBlock(Token $token, $condition, $begin){
		$this->symbol		= $token->symbol;
		$this->line			= $token->line;
		$this->char			= $token->char;
		$this->condition	= $condition;
		$this->begin		= $begin;
	}
}

class FunctionDefinition extends Keyword{
	public $address;
	public $code;
	
	public function FunctionDefinition(Token $token, $argument, $code){
		$this->symbol	= $token->symbol;
		$this->line		= $token->line;
		$this->char		= $token->char;
		$this->argument	= $argument;
		$this->code		= $code;
	}
}

class FunctionCall extends Variable{
	public $argument;
	
	public function FunctionCall(Token $token, &$address, $argument){
		$this->symbol	= $token->symbol;
		$this->line 	= $token->line;
		$this->char		= $token->char;
		$this->address	=& $address;
		$this->argument	= $argument;
	}

}

class UnconditionalJump extends InternalInstruction{
	public $address;
}

class Loop extends InternalInstruction{
	public $address;
	public $count;
	public $times;
	
	public function Loop($begin, $times){
		$this->address	= $begin;
		$this->times	= $times;
	}
}


/*
	SCANNER
*/
class Scanner{
	
	const EOL			= "/^(\r?\n)$/";
	const SOURCE_FILE	= 0;
	const SOURCE_TEXT	= 1;
	
	protected $file;
	protected $symbol;
	protected $line = 1;
	protected $char = 1;
		
	public function Scanner($source, $type = self::SOURCE_FILE){
		
		if($type == self::SOURCE_TEXT){
			$this->file = fopen('php://memory','r+');
			fwrite($this->file, $source);
			rewind($this->file);
		} else
			if(!($this->file = fopen($source, 'r')))
				throw new Exception('Could not open file.');			
	}
		
	public function scan(){
			
		if(($symbol = fgetc($this->file)) === false)
			return false;
			
		$this->char		= ftell($this->file);
		$this->symbol	= $symbol;
					
		if(preg_match(self::EOL, $symbol)){
			$this->line++;
			$symbol = self::EOL;
			//return($this->scan());
		}
															
		return array('symbol' => $symbol, 'line' => $this->line, 'char' => $this->char);				
	}
		
	public function backtrack($n){
		fseek($this->file, $n, SEEK_CUR);
	}
	
	public function reset(){
		rewind($this->file);
		$this->line = $this->char = 1;
	}
		
	public function jumpNextLine(){
		while(($char = fgetc($this->file)) !== false)
			if(preg_match(self::EOL, $char)){
				$this->line++;
				return true;
			}
		return false;
	}
}

/*
	LEXER
*/	
class Lexer{
	
	const DTK_TKN = 0;
						
	protected $scanner;
		
	/*
		Dynamic properties obtained from Grammar object on construct
		
		+ numbers
		+ operators
		+ delimiters
		+ identifiers
		+ commentsLine
		+ singleLiterals
		+ doubleLiterals
		+ commentsBlockOpen
		+ commentsBlockClosed	
	*/
						
	public function Lexer(Scanner $scanner, Language $grammar){
		$this->scanner	= $scanner;	
		$syntax = $grammar->getSyntax();
			
		foreach($syntax as $property => $syntax)
			$this->$property = $syntax;			
	}
			
	public function nextToken(){
									
		// get first char
		while($char = $this->scanner->scan()){
										
			// catch white space & EOL
			if(($char['symbol'] == ' '))
				continue;
			if(preg_match(Scanner::EOL, $char['symbol']))
				return $token;

			// catch block comments
			if($this->seek($this->commentsBlockOpen, $char)){
				while($char && !$this->seek($this->commentsBlockClosed, $char))
					$char = $this->scanner->scan();
				continue;
			}
				
			// catch line comments
			if($this->seek($this->commentsLine, $char))
				if($this->scanner->jumpNextLine())
					continue;
				else
					break;
				
			// catch single literals
			if($this->seek($this->singleLiterals, $char)){
				
				$ln = $char['line'];
				$ch = $char['char'];
				$tk = '';
				
				while(($char = $this->scanner->scan()) && !$this->seek($this->singleLiterals, $char))
					$tk .= $char['symbol'];
					
				if(!$char)
					throw new Exception('Unexpected EOF.');
				
				return new Token($tk, Interpreter::STR, $ln, $ch);
			}
				
			// catch double literals
			if($this->seek($this->doubleLiterals, $char)){
				
				$ln = $char['line'];
				$ch = $char['char'];
				$tk = '';
			
				while(($char = $this->scanner->scan()) && !$this->seek($this->doubleLiterals, $char))
					$tk .= $char['symbol'];

				if(!$char)
					throw new Exception('Unexpected EOF.');
	
				return new Token($tk, Interpreter::STR, $ln, $ch);
			}
			
			// catch numbers
			if($number = $this->match($this->numbers, $char))
				return $number;	
			
			// catch keywords
			if($identifier = $this->match($this->identifiers, $char)){
				foreach($this->keywords as $token)
					if($token->symbol == $identifier->symbol){
						$token->line	= $identifier->line;
						$token->char	= $identifier->char;
						return $token;
					}
			
				return $identifier;
			}
			
			// catch operators
			if($operator = $this->seek($this->operators, $char))
				return $operator;
						
			// catch delimiters
			if($delimiter = $this->seek($this->delimiters, $char))
				return $delimiter;								
		}
						
		return false;
	}
	
	public function reset(){
		$this->scanner->reset();
	}
				
	protected function match($pntr, $char){
		
		if(!is_array($char))
			throw new Exception('$char is expected to be an Array');
			
		$ln	= $char['line'];
		$ch	= $char['char'];
		$tk	= '';
		$n	= 0;
		
		$rule = $pntr->symbol;
		
		while(preg_match($rule, $tk.$char['symbol'])){
			$tk .= $char['symbol'];
			if(!($char = $this->scanner->scan()))
				break;
			$n++;
		}
			
		if(strlen($tk) > 0){
			if($char)
				$this->scanner->backtrack(-1);
							
			return new Token($tk, $pntr->type, $ln, $ch);
		}
			
		$this->scanner->backtrack(-$n);
		return false;
	}
		
	protected function seek(&$pntr, $char){
	
		if(!is_array($char))
			throw new Exception('$char is expected to be an Array');
				
		$ln	= $char['line'];
		$ch	= $char['char'];
		$tk	= '';
		$n	= 0;

		while(isset($pntr[$char['symbol']])){
		
			$pntr	=& $pntr[$char['symbol']];
			$tk		.= $char['symbol'];
					
			if(!($char = $this->scanner->scan()))
				break;
			$n++;
		}
			
		if(isset($pntr[self::DTK_TKN])){
			if($char)
				$this->scanner->backtrack(-1);
			$token = $pntr[self::DTK_TKN];
			$token->line = $ln;
			$token->char = $ch;
			return $token;
		}
			
		$this->scanner->backtrack(-$n);	
		return false;
	}
			
}

/*
	LANGUAGE
*/
abstract class Language{

	public $owner;
		
	protected $numbers;
	protected $keywords;
	protected $identifiers;	
	protected $treeOperators			= array();
	protected $treeDelimiters			= array();
	protected $treeStrLiteralSingle		= array();
	protected $treeStrLiteralDouble		= array();
	protected $treeComBlockOpen			= array();
	protected $treeComBlockClosed		= array();
	protected $treeComLine				= array();
				
	public function getSyntax(){
		return array(
			'numbers'				=> $this->numbers,
			'keywords'				=> $this->keywords,
			'identifiers'			=> $this->identifiers,
			'operators'				=> $this->treeOperators,
			'delimiters'			=> $this->treeDelimiters,
			'commentsLine'			=> $this->treeComLine,
			'singleLiterals'		=> $this->treeStrLiteralSingle,
			'doubleLiterals'		=> $this->treeStrLiteralDouble,
			'commentsBlockOpen'		=> $this->treeComBlockOpen,
			'commentsBlockClosed'	=> $this->treeComBlockClosed	
		);
	}
	
	public function setKeywords($keywords){
		foreach($keywords as $token)
			if(!$token instanceof Token)
				throw new Exception('Token object expected.');
			else
				$token->type = Interpreter::KEYWORD;
				
		$this->keywords = $keywords;
	}
				
	public function setRulesNumbers(Token $numbers){
		$numbers->type = Interpreter::CONSTANT;
		$this->numbers = $numbers;
	}
		
	public function setRulesIdentifiers(Token $identifiers){
		$identifiers->type = Interpreter::IDENTIFIER;
		$this->identifiers = $identifiers;
	}
		
	public function setOperators($operators){
		if(!is_array($operators))
			throw new Exception('Array expected');
		else foreach($operators as $token)
			if(!$token instanceof Token)
				throw new Exception('Token object expected');
			else
				$token->type = Interpreter::OPERATOR;
				
		$this->buildTokenTree($this->treeOperators, $operators);
	}
		
	public function setDelimiters($delimiters){
		if(!is_array($delimiters))
			throw new Exception('Array expected');
		else foreach($delimiters as $token)
			if(!$token instanceof Token)
				throw new Exception('Token object expected');
			else
				$token->type = Interpreter::DELIMITER;
				
		$this->buildTokenTree($this->treeDelimiters, $delimiters);
				
	}
			
	public function setRulesComments(Token $line, Token $blockOpen, Token $blockClose){
		$line->type			= Interpreter::DELIMITER;
		$blockOpen->type	= Interpreter::DELIMITER;
		$blockClose->type	= Interpreter::DELIMITER;
		$this->buildTokenTree($this->treeComLine,			is_array($line)			? $line			: array($line));
		$this->buildTokenTree($this->treeComBlockOpen,		is_array($blockOpen)	? $blockOpen	: array($blockOpen));
		$this->buildTokenTree($this->treeComBlockClosed,	is_array($blockClose)	? $blockClosed	: array($blockClose));
	}
		
	public function setRulesStringLiterals(Token $single, Token $double){
		$single->type = Interpreter::DELIMITER;
		$double->type = Interpreter::DELIMITER;
		$this->buildTokenTree($this->treeStrLiteralSingle, is_array($single)	? $single	: array($single));
		$this->buildTokenTree($this->treeStrLiteralDouble, is_array($double)	? $double	: array($double));			
	}
				
	protected function buildTokenTree(&$tree, $tokens){
			
		if(!is_array($tokens))
			throw new Exception('Array expected.');
				
		$root = array();
		foreach($tokens as $token){
			$pntr =& $root;
			for($i = 0; $i < strlen($token->symbol); $i++){		
				if(!isset($pntr[$token->symbol[$i]]))
					$pntr[$token->symbol[$i]] = array();
				$pntr =& $pntr[$token->symbol[$i]];
			}
			$pntr[0] = $token;
		}
			
		$tree = $root;
	}
		
}

?>
